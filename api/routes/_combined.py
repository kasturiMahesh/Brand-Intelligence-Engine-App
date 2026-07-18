"""Health check, crawl management, and analytics routes."""
from fastapi import APIRouter
from config.database import get_content_collection
from workers.queue_manager import queue_manager

router = APIRouter()

# ─── Health ───────────────────────────────────────────────────────────────────
health_router = APIRouter()

@health_router.get("/")
async def health():
    queue_depth = await queue_manager.get_queue_depth()
    return {"status": "ok", "queue_depth": queue_depth}

# ─── Crawl ────────────────────────────────────────────────────────────────────
crawl_router = APIRouter()

@crawl_router.get("/queue")
async def queue_stats():
    depth = await queue_manager.get_queue_depth()
    return {"queue_depth": depth}

# ─── Analytics ────────────────────────────────────────────────────────────────
analytics_router = APIRouter()

@analytics_router.get("/summary")
async def analytics_summary(query: str):
    col = get_content_collection()
    pipeline = [
        {"$match": {"query": query}},
        {"$group": {
            "_id": None,
            "total_docs":        {"$sum": 1},
            "avg_relevance":     {"$avg": "$relevance_score"},
            "avg_confidence":    {"$avg": "$confidence_score"},
            "sentiment_dist":    {"$push": "$sentiment"},
            "credibility_dist":  {"$push": "$source_credibility"},
            "total_words":       {"$sum": "$word_count"},
            "domains":           {"$addToSet": "$domain"},
        }},
    ]
    result = await col.aggregate(pipeline).to_list(length=1)
    if not result:
        return {"query": query, "message": "No data found"}

    r = result[0]
    sentiments = r.get("sentiment_dist", [])
    credibility = r.get("credibility_dist", [])

    def dist(lst):
        counts = {}
        for item in lst:
            counts[item] = counts.get(item, 0) + 1
        return counts

    return {
        "query":            query,
        "total_documents":  r["total_docs"],
        "unique_domains":   len(r.get("domains", [])),
        "avg_relevance":    round(r["avg_relevance"], 3),
        "avg_confidence":   round(r["avg_confidence"], 3),
        "total_words":      r["total_words"],
        "sentiment":        dist(sentiments),
        "source_credibility": dist(credibility),
    }
