"""
Web Intelligence Ingestion Engine — Main Entry Point
Production-grade brand intelligence data foundation.
"""
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from api.routes import search, crawl, content, health, analytics
from config.settings import settings
from utils.logger import get_logger
from workers.queue_manager import queue_manager
from workers.crawl_worker import CrawlWorker

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of background services."""
    logger.info("🚀 Starting Web Intelligence Engine...")
    await queue_manager.initialize()
    worker = CrawlWorker(concurrency=settings.WORKER_CONCURRENCY)
    worker_task = asyncio.create_task(worker.run())
    logger.info(f"✅ {settings.WORKER_CONCURRENCY} crawl workers active")
    yield
    logger.info("⏹ Shutting down...")
    worker_task.cancel()
    await queue_manager.close()

app = FastAPI(
    title="Web Intelligence Ingestion Engine",
    description="Production-grade brand intelligence data foundation",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(crawl.router, prefix="/api/v1/crawl", tags=["Crawl"])
app.include_router(content.router, prefix="/api/v1/content", tags=["Content"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1,
        loop="asyncio",
        http="httptools",
    )
