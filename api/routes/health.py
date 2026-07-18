"""Health check routes."""
from fastapi import APIRouter
from workers.queue_manager import queue_manager

router = APIRouter()

@router.get("/")
async def health():
    queue_depth = await queue_manager.get_queue_depth()
    return {"status": "ok", "service": "web-intelligence-engine", "queue_depth": queue_depth}
