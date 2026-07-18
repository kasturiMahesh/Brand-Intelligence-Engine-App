"""
Search route v3 — batch PostgreSQL insert (single round trip for 30 URLs).
"""
import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from config.database import AsyncSessionLocal
from schemas.models import SearchRequest, SearchResponse, SearchResult, JobStatus
from workers.search_engine import search_orchestrator
from workers.queue_manager import queue_manager
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def submit_search(req: SearchRequest):
    """
    v3: Single batch INSERT for all URLs (vs N sequential inserts in v2).
    Enriches url_hash on results list in-memory before enqueue.
    """
    job_id = str(uuid.uuid4())

    try:
        results = await search_orchestrator.search(
            query=req.query,
            max_results=req.max_results,
            engine=req.search_engine,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Search error: {e}")

    if not results:
        raise HTTPException(status_code=404, detail="No results found")

    # Build all rows + enrich url_hash in one pass (no await in loop)
    rows = []
    for item in results:
        url_hash = SearchResult.make_url_hash(item["url"])
        item["url_hash"] = url_hash
        rows.append({
            "query":    req.query,
            "url":      item["url"],
            "url_hash": url_hash,
            "title":    item.get("title", ""),
            "snippet":  item.get("snippet", ""),
            "rank":     item.get("rank"),
            "domain":   item.get("domain", ""),
        })

    # Single batch INSERT — one round trip for all URLs
    stmt = (
        pg_insert(SearchResult.__table__)
        .values(rows)
        .on_conflict_do_nothing(index_elements=[SearchResult.url_hash])
    )
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(stmt)
            await session.commit()
    except Exception as exc:
        logger.exception("Database insert failed for search results")
        raise HTTPException(
            status_code=500,
            detail="Could not save search results. Please try again later.",
        )

    # Enqueue (already has url_hash set on each item)
    try:
        queued = await queue_manager.enqueue_batch(
            job_id,
            [{**r, "query": req.query} for r in results],
        )
    except Exception as exc:
        logger.exception("Redis enqueue failed for job %s", job_id)
        raise HTTPException(
            status_code=500,
            detail="Could not enqueue search results for processing.",
        )

    logger.info(f"job {job_id[:8]} {len(results)} urls stored, {queued} queued")

    return SearchResponse(
        job_id=job_id,
        query=req.query,
        urls_found=len(results),
        queued=queued,
        message=f"{queued} URLs queued. Poll /api/v1/search/status/{job_id}",
    )


@router.get("/status/{job_id}", response_model=JobStatus)
async def job_status(job_id: str):
    stats = await queue_manager.get_job_stats(job_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Job not found")
    total     = stats.get("total", 0)
    completed = stats.get("completed", 0)
    failed    = stats.get("failed", 0)
    skipped   = stats.get("skipped", 0)
    done      = completed + failed + skipped
    return JobStatus(
        job_id=job_id,
        query="",
        total_urls=total,
        pending=max(total - done, 0),
        processing=0,
        completed=completed,
        failed=failed,
        skipped=skipped,
        progress_pct=round(done / total * 100 if total else 0, 1),
    )
