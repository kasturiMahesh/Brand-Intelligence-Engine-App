"""Analytics routes v2 — aligned with canonical schema field names."""
from fastapi import APIRouter, Query
from config.database import get_content_collection

router = APIRouter()


@router.get("/summary")
async def analytics_summary(query: str = Query(..., min_length=2)):
    col = get_content_collection()
    pipeline = [
        {"$match": {"query": query}},
        {"$group": {
            "_id":                None,
            "total_docs":         {"$sum": 1},
            "avg_relevance":      {"$avg": "$relevance_score"},
            "avg_confidence":     {"$avg": "$confidence_score"},
            "avg_word_count":     {"$avg": "$word_count"},
            "total_words":        {"$sum": "$word_count"},
            "sentiment_dist":     {"$push": "$sentiment"},
            "credibility_dist":   {"$push": "$source_credibility"},
            "language_dist":      {"$push": "$language"},
            "domains":            {"$addToSet": "$source_domain"},
        }},
    ]
    result = await col.aggregate(pipeline).to_list(length=1)
    if not result:
        return {"query": query, "message": "No processed data found"}

    r = result[0]
    def dist(lst):
        d = {}
        for item in lst:
            d[item] = d.get(item, 0) + 1
        return d

    return {
        "query":              query,
        "total_documents":    r["total_docs"],
        "unique_domains":     len(r.get("domains", [])),
        "avg_relevance":      round(r["avg_relevance"], 3),
        "avg_confidence":     round(r["avg_confidence"], 3),
        "avg_word_count":     round(r["avg_word_count"], 0),
        "total_words":        r["total_words"],
        "sentiment":          dist(r.get("sentiment_dist", [])),
        "source_credibility": dist(r.get("credibility_dist", [])),
        "languages":          dist(r.get("language_dist", [])),
        "top_domains":        sorted(r.get("domains", []))[:15],
    }


@router.get("/domains")
async def domain_breakdown(query: str = Query(...)):
    col = get_content_collection()
    pipeline = [
        {"$match": {"query": query}},
        {"$group": {
            "_id":            "$source_domain",
            "count":          {"$sum": 1},
            "avg_relevance":  {"$avg": "$relevance_score"},
            "avg_confidence": {"$avg": "$confidence_score"},
            "credibility":    {"$first": "$source_credibility"},
        }},
        {"$sort": {"avg_relevance": -1}},
        {"$limit": 25},
    ]
    results = await col.aggregate(pipeline).to_list(length=25)
    return {
        "query": query,
        "domains": [
            {
                "domain":         r["_id"],
                "doc_count":      r["count"],
                "avg_relevance":  round(r["avg_relevance"], 3),
                "avg_confidence": round(r["avg_confidence"], 3),
                "credibility":    r["credibility"],
            }
            for r in results
        ],
    }


@router.get("/quality")
async def quality_distribution(query: str = Query(...)):
    """Relevance score distribution for a query — useful for threshold tuning."""
    col = get_content_collection()
    pipeline = [
        {"$match": {"query": query}},
        {"$bucket": {
            "groupBy":    "$relevance_score",
            "boundaries": [0.0, 0.40, 0.55, 0.70, 0.85, 1.01],
            "default":    "other",
            "output":     {
                "count":   {"$sum": 1},
                "avg_wc":  {"$avg": "$word_count"},
            },
        }},
    ]
    try:
        results = await col.aggregate(pipeline).to_list(length=10)
    except Exception:
        results = []
    labels = ["0.00-0.40", "0.40-0.55", "0.55-0.70", "0.70-0.85", "0.85-1.00"]
    return {
        "query":        query,
        "distribution": [
            {
                "range": labels[i] if i < len(labels) else "other",
                "count": r.get("count", 0),
                "avg_word_count": round(r.get("avg_wc", 0)),
            }
            for i, r in enumerate(results)
        ],
    }
