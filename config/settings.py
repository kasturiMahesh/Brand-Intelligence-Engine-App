"""
Configuration management — all settings from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Database — PostgreSQL (raw URL storage)
    POSTGRES_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/web_intelligence"
    
    # Database — MongoDB (processed JSON storage)
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB: str = "web_intelligence"
    
    # Redis (queue + caching)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_QUEUE_KEY: str = "crawl:queue"
    REDIS_PROCESSING_KEY: str = "crawl:processing"
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # Search APIs
    SERPAPI_KEY: Optional[str] = None
    GOOGLE_CSE_KEY: Optional[str] = None
    GOOGLE_CSE_ID: Optional[str] = None
    BING_API_KEY: Optional[str] = None
    
    # Claude AI
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    
    # Workers
    WORKER_CONCURRENCY: int = 20
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: float = 2.0  # exponential backoff seconds
    REQUEST_TIMEOUT: int = 25
    REQUESTS_PER_DOMAIN_PER_MINUTE: int = 10  # Rate limiting per domain
    
    # Scraping
    USE_HEADLESS: bool = False  # Playwright fallback
    ROTATE_USER_AGENTS: bool = True
    MIN_RELEVANCE_SCORE: float = 0.35
    MAX_CONTENT_TOKENS: int = 8000
    
    # JSON file output
    WRITE_JSON_FILE: bool = True
    JSON_OUTPUT_DIR: str = "./json_output"


settings = Settings()
