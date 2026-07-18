"""Crawl queue management routes."""
from fastapi import APIRouter
from workers.queue_manager import queue_manager

router = APIRouter()

@router.get("/queue")
async def queue_stats():
    depth = await queue_manager.get_queue_depth()
    return {"queue_depth": depth, "status": "running"}
