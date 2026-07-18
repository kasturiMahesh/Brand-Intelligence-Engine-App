"""
Content retrieval API v2 — aligned with canonical document schema.
"""
from fastapi import APIRouter, Query, HTTPException
from config.database import get_content_collection
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Fields excluded by default (large text — fetch explicitly when needed)
DEFAULT_EXCLUDE = {"_id": 0, "clean_text": 0, "embedding_text": 0}
FULL_EXCLUDE    = {"_id": 0}


@router.get("/")
async def get_content(
    query:         str   = Query(..., min_length=2),
    min_relevance: float = Query(0.40, ge=0.0, le=1.0),
    limit:         int   = Query(20, ge=1, le=100),
    skip:          int   = Query(0, ge=0),
    sort_by:       str   = Query("relevance_score"),
    language:      str   = Query(None),
    credibility:   str   = Query(None),   # high|medium|low
    include_text:  bool  = Query(False),  # include clean_text in response
):
    """
    Retrieve processed content for a query.
    Returns documents matching the canonical v2 schema.
    """
    col = get_content_collection()

    # Build filter
    filt = {"query": query, "relevance_score": {"$gte": min_relevance}}
    if language:
        filt["language"] = language
    if credibility and credibility in {"high", "medium", "low"}:
        filt["source_credibility"] = credibility

    sort_field = sort_by if sort_by in {"relevance_score", "confidence_score", "timestamp", "word_count"} else "relevance_score"
    projection = FULL_EXCLUDE if include_text else DEFAULT_EXCLUDE

    cursor = (
        col.find(filt, projection)
        .sort(sort_field, -1)
        .skip(skip)
        .limit(limit)
    )
    docs  = await cursor.to_list(length=limit)
    total = await col.count_documents(filt)

    return {
        "query":     query,
        "total":     total,
        "returned":  len(docs),
        "page":      skip // limit + 1,
        "results":   docs,
    }


@router.get("/search")
async def fulltext_search(
    q:             str   = Query(..., min_length=3, description="Full-text search term"),
    query:         str   = Query(None, description="Filter by original search query"),
    min_relevance: float = Query(0.40, ge=0.0, le=1.0),
    limit:         int   = Query(20, ge=1, le=50),
):
    """Full-text search across content_summary, relevant_text, key_points, title."""
    col = get_content_collection()
    filt = {
        "$text": {"$search": q},
        "relevance_score": {"$gte": min_relevance},
    }
    if query:
        filt["query"] = query

    cursor = (
        col.find(filt, {**DEFAULT_EXCLUDE, "score": {"$meta": "textScore"}})
        .sort([("score", {"$meta": "textScore"})])
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return {"search_term": q, "returned": len(docs), "results": docs}


@router.get("/{url_hash}")
async def get_by_hash(url_hash: str, full: bool = Query(False)):
    """Get a specific document by URL hash. full=true includes clean_text and embedding_text."""
    col  = get_content_collection()
    proj = FULL_EXCLUDE if full else DEFAULT_EXCLUDE
    doc  = await col.find_one({"url_hash": url_hash}, proj)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/domain/{domain}")
async def get_by_domain(
    domain:        str,
    query:         str   = Query(None),
    min_relevance: float = Query(0.40),
    limit:         int   = Query(20),
):
    """Get all content from a specific source domain."""
    col  = get_content_collection()
    filt = {"source_domain": domain, "relevance_score": {"$gte": min_relevance}}
    if query:
        filt["query"] = query
    cursor = col.find(filt, DEFAULT_EXCLUDE).sort("relevance_score", -1).limit(limit)
    docs   = await cursor.to_list(length=limit)
    return {"domain": domain, "returned": len(docs), "results": docs}
