"""
Queue Manager v3 — Maximum throughput Redis operations.

Performance wins vs v2:
  - enqueue_batch: lock checks batched via pipeline MGET (1 round trip for all 30 URLs)
  - Dequeue: zpopmin count=3 (batch pop) → fed into worker via internal asyncio.Queue
  - All Redis operations use pipeline where possible (1 RTT vs N)
  - Rate limit: sorted set window uses pipeline (zremrange + zcard + zadd in 1 RTT)
  - mark_complete: merged into single hincrby pipeline
  - Removed per-item loop awaits in enqueue_batch
  - Connection pool raised to 100
"""
import asyncio
import json
import time
from typing import Optional, Dict

import redis.asyncio as aioredis
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_BATCH_POP_SIZE = 5   # how many jobs to pop at once from sorted set


class QueueManager:

    QUEUE_KEY     = "wi:queue"
    LOCK_KEY      = "wi:lock:{}"
    DLQ_KEY       = "wi:dlq"
    RATE_KEY      = "wi:rate:{}"
    JOB_STATS_KEY = "wi:job:{}:stats"

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        # Internal asyncio queue bridges batch-pop and per-worker dequeue
        self._local_q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._poller_running = False

    async def initialize(self):
        self._redis = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=100,
        )
        await self._redis.ping()
        # Start background batch poller
        asyncio.ensure_future(self._batch_poller())
        self._poller_running = True
        logger.info("✅ Redis queue ready (batch poller started)")

    async def close(self):
        self._poller_running = False
        if self._redis:
            await self._redis.aclose()

    # ── Background batch poller ───────────────────────────────────────────────

    async def _batch_poller(self):
        """
        Continuously pops up to _BATCH_POP_SIZE jobs from Redis sorted set
        and places them into the local asyncio.Queue.
        This decouples Redis I/O from individual worker dequeue calls,
        and allows batch pops (fewer Redis RTTs per job).
        """
        while self._poller_running:
            try:
                if self._local_q.qsize() >= 50:
                    # Local queue sufficiently full — back off
                    await asyncio.sleep(0.1)
                    continue

                results = await self._redis.zpopmin(self.QUEUE_KEY, _BATCH_POP_SIZE)
                if not results:
                    await asyncio.sleep(0.2)
                    continue

                # Batch update locks in one pipeline
                pipe = self._redis.pipeline(transaction=False)
                jobs = []
                for payload_str, _score in results:
                    try:
                        job = json.loads(payload_str)
                        jobs.append(job)
                        pipe.set(
                            self.LOCK_KEY.format(job["url_hash"]),
                            "processing",
                            ex=300,
                        )
                    except (json.JSONDecodeError, KeyError):
                        continue
                if jobs:
                    await pipe.execute()
                    for job in jobs:
                        await self._local_q.put(job)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batch poller error: {e}")
                await asyncio.sleep(1)

    # ── Dequeue (workers call this) ───────────────────────────────────────────

    async def dequeue(self, timeout: float = 1.5) -> Optional[dict]:
        """Non-blocking get from local asyncio queue."""
        try:
            return self._local_q.get_nowait()
        except asyncio.QueueEmpty:
            try:
                return await asyncio.wait_for(self._local_q.get(), timeout=timeout)
            except asyncio.TimeoutError:
                return None

    # ── Enqueue batch ─────────────────────────────────────────────────────────

    async def enqueue_batch(self, job_id: str, urls: list[dict]) -> int:
        """
        Batch enqueue all URLs.
        Single MGET to check all lock keys (1 RTT instead of N).
        Single pipeline to write all new jobs (1 RTT).
        """
        if not urls:
            return 0

        lock_keys = [self.LOCK_KEY.format(u["url_hash"]) for u in urls]

        # 1 RTT: check all locks at once
        existing = await self._redis.mget(*lock_keys)

        pipe     = self._redis.pipeline(transaction=False)
        now      = time.time()
        enqueued = 0

        for item, already_locked in zip(urls, existing):
            if already_locked:
                continue

            url_hash = item["url_hash"]
            payload  = json.dumps({
                "job_id":    job_id,
                "url_hash":  url_hash,
                "url":       item["url"],
                "query":     item.get("query", ""),
                "domain":    item.get("domain", ""),
                "rank":      item.get("rank", 99),
                "enqueued_at": now,
                "retries":   0,
            }, separators=(",", ":"))  # compact JSON (no extra spaces)

            score = item.get("rank", 99) + now / 1e9
            pipe.zadd(self.QUEUE_KEY, {payload: score})
            pipe.set(self.LOCK_KEY.format(url_hash), "queued", ex=3600)
            pipe.hincrby(self.JOB_STATS_KEY.format(job_id), "total", 1)
            enqueued += 1

        if enqueued:
            await pipe.execute()

        logger.info(f"Enqueued {enqueued}/{len(urls)} → job {job_id[:8]}")
        return enqueued

    # ── Retry / fail ──────────────────────────────────────────────────────────

    async def requeue_with_backoff(self, job: dict, error: str) -> bool:
        retries = job.get("retries", 0) + 1
        if retries > settings.MAX_RETRIES:
            await self._dlq(job, error)
            return False

        delay = settings.RETRY_BACKOFF_BASE ** retries
        job["retries"]    = retries
        job["last_error"] = error[:120]
        score = time.time() + delay

        pipe = self._redis.pipeline(transaction=False)
        pipe.zadd(self.QUEUE_KEY, {json.dumps(job, separators=(",", ":")): score})
        pipe.set(self.LOCK_KEY.format(job["url_hash"]), f"retry:{retries}", ex=int(delay) + 60)
        await pipe.execute()
        return True

    async def mark_complete(self, job: dict, status: str = "completed"):
        pipe = self._redis.pipeline(transaction=False)
        pipe.set(self.LOCK_KEY.format(job["url_hash"]), status, ex=86400)
        pipe.hincrby(self.JOB_STATS_KEY.format(job["job_id"]), status, 1)
        await pipe.execute()

    async def _dlq(self, job: dict, error: str):
        job["final_error"] = error
        job["failed_at"]   = time.time()
        await self._redis.lpush(self.DLQ_KEY, json.dumps(job, separators=(",", ":")))
        await self._redis.hincrby(self.JOB_STATS_KEY.format(job["job_id"]), "failed", 1)

    # ── Rate limiting ─────────────────────────────────────────────────────────

    async def check_rate_limit(self, domain: str) -> bool:
        """Sliding window — all ops in one pipeline (1 RTT)."""
        key = self.RATE_KEY.format(domain)
        now = time.time()
        window_start = now - 60.0

        pipe = self._redis.pipeline(transaction=False)
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, 90)
        results = await pipe.execute()
        count = results[1]
        return count < settings.REQUESTS_PER_DOMAIN_PER_MINUTE

    # ── Stats ─────────────────────────────────────────────────────────────────

    async def get_job_stats(self, job_id: str) -> Dict[str, int]:
        raw = await self._redis.hgetall(self.JOB_STATS_KEY.format(job_id))
        return {k: int(v) for k, v in raw.items()}

    async def get_queue_depth(self) -> int:
        return await self._redis.zcard(self.QUEUE_KEY)


queue_manager = QueueManager()
