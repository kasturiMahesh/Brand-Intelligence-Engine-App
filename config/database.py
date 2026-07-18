"""
Database connection management — async PostgreSQL + MongoDB.
"""
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from motor.motor_asyncio import AsyncIOMotorClient
from schemas.models import Base
from config.settings import settings
from utils.logger import get_logger
from typing import AsyncGenerator

logger = get_logger(__name__)


def _normalize_postgres_url(url: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if query.get("sslmode") == "require":
        query.pop("sslmode")
        query["ssl"] = "true"
        parsed = parsed._replace(query=urlencode(query))
    return urlunparse(parsed)


# ─── PostgreSQL ───────────────────────────────────────────────────────────────

engine = create_async_engine(
    _normalize_postgres_url(settings.POSTGRES_URL),
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def init_postgres():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ PostgreSQL tables initialized")

async def get_pg_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ─── MongoDB ─────────────────────────────────────────────────────────────────

_mongo_client: AsyncIOMotorClient = None

def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(
            settings.MONGO_URL,
            maxPoolSize=50,
            minPoolSize=5,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
    return _mongo_client

def get_mongo_db():
    return get_mongo_client()[settings.MONGO_DB]

def get_content_collection():
    return get_mongo_db()["processed_content"]

async def init_mongo():
    """Create indexes for efficient querying — aligned with v2 schema."""
    col = get_content_collection()

    # Primary lookup indexes
    await col.create_index([("url_hash", 1)], unique=True)
    await col.create_index([("query", 1)])

    # Analytical indexes
    await col.create_index([("relevance_score", -1)])
    await col.create_index([("confidence_score", -1)])
    await col.create_index([("source_domain", 1)])      # renamed from domain
    await col.create_index([("timestamp", -1)])
    await col.create_index([("language", 1)])
    await col.create_index([("sentiment", 1)])
    await col.create_index([("source_credibility", 1)])
    await col.create_index([("content_hash", 1)])       # incremental crawl dedup

    # Compound indexes for common query patterns
    await col.create_index([("query", 1), ("relevance_score", -1)])
    await col.create_index([("query", 1), ("source_domain", 1)])
    await col.create_index([("query", 1), ("timestamp", -1)])

    # Full-text search across content fields
    await col.create_index([
        ("content_summary", "text"),
        ("relevant_text", "text"),
        ("key_points", "text"),
        ("title", "text"),
    ], name="content_fulltext")

    logger.info("✅ MongoDB indexes initialized (v2 schema)")
