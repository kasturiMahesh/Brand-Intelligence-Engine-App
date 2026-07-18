"""
Database schemas v2 — canonical standardised document schema.
MongoDB document now matches the exact required output structure.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Index, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
import hashlib
import re


# ─── PostgreSQL ───────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass

class URLStatus(str, Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"
    SKIPPED    = "skipped"

class SearchResult(Base):
    __tablename__ = "search_results"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    query        = Column(String(500), nullable=False, index=True)
    url          = Column(String(2000), nullable=False)
    url_hash     = Column(String(64), nullable=False, unique=True)
    title        = Column(String(500))
    snippet      = Column(Text)
    rank         = Column(Integer)
    domain       = Column(String(255), index=True)
    status       = Column(SAEnum(URLStatus), default=URLStatus.PENDING, index=True)
    retry_count  = Column(Integer, default=0)
    error_msg    = Column(Text)
    content_hash = Column(String(64))
    crawled_at   = Column(DateTime(timezone=True))
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_query_status", "query", "status"),
        Index("ix_domain_created", "domain", "created_at"),
    )

    @staticmethod
    def make_url_hash(url: str) -> str:
        return hashlib.sha256(url.strip().lower().encode()).hexdigest()


class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    url_hash    = Column(String(64), nullable=False, index=True)
    stage       = Column(String(50))
    status      = Column(String(20))
    duration_ms = Column(Integer)
    message     = Column(Text)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ─── MongoDB — Canonical Document Schema ─────────────────────────────────────

class HeadingsSchema(BaseModel):
    """Structured heading map — always present, always typed."""
    h1: List[str] = Field(default_factory=list)
    h2: List[str] = Field(default_factory=list)
    h3: List[str] = Field(default_factory=list)

    @field_validator("h1", "h2", "h3", mode="before")
    @classmethod
    def ensure_string_list(cls, v):
        if not isinstance(v, list):
            return []
        return [str(x).strip()[:200] for x in v if x]


class ProcessedContent(BaseModel):
    """
    Canonical document schema stored in MongoDB.
    Every field is required and typed — no missing fields, no nulls.
    This is the single source of truth for downstream AI consumption.
    """
    # ── Identity ────────────────────────────────────────────────────────────
    url:              str
    url_hash:         str
    query:            str
    source_domain:    str          = ""

    # ── Content ─────────────────────────────────────────────────────────────
    title:            str          = ""
    meta_description: str          = ""
    headings:         HeadingsSchema = Field(default_factory=HeadingsSchema)
    clean_text:       str          = ""   # full cleaned body text
    relevant_text:    str          = ""   # AI-filtered relevant sections only
    content_summary:  str          = ""   # 2-4 sentence factual summary
    key_points:       List[str]    = Field(default_factory=list)

    # ── Scoring ─────────────────────────────────────────────────────────────
    relevance_score:   float       = 0.0   # 0.0–1.0
    confidence_score:  float       = 0.0   # content quality proxy
    sentiment:         str         = "neutral"  # positive|neutral|negative
    source_credibility:str         = "medium"   # high|medium|low

    # ── Metadata ─────────────────────────────────────────────────────────────
    word_count:        int         = 0
    language:          str         = "en"
    author:            str         = ""
    publish_date:      str         = ""
    canonical_url:     str         = ""

    # ── Dedup + embedding ────────────────────────────────────────────────────
    content_hash:      str         = ""
    embedding_text:    str         = ""   # clean text for vector DB

    # ── Timestamp ────────────────────────────────────────────────────────────
    timestamp:         datetime    = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("relevance_score", "confidence_score", mode="before")
    @classmethod
    def clamp_float(cls, v):
        try:
            f = float(v)
            return round(max(0.0, min(1.0, f)), 4)
        except (TypeError, ValueError):
            return 0.0

    @field_validator("sentiment", mode="before")
    @classmethod
    def validate_sentiment(cls, v):
        v = str(v).lower().strip()
        return v if v in {"positive", "neutral", "negative"} else "neutral"

    @field_validator("source_credibility", mode="before")
    @classmethod
    def validate_credibility(cls, v):
        v = str(v).lower().strip()
        return v if v in {"high", "medium", "low"} else "medium"

    @field_validator("word_count", mode="before")
    @classmethod
    def ensure_int(cls, v):
        try:
            return max(0, int(v))
        except (TypeError, ValueError):
            return 0

    @field_validator("key_points", mode="before")
    @classmethod
    def clean_key_points(cls, v):
        if not isinstance(v, list):
            return []
        return [str(x).strip()[:120] for x in v if x and str(x).strip()][:7]

    @field_validator("title", "meta_description", "clean_text", "content_summary",
                     "relevant_text", "embedding_text", "url", "url_hash", "query",
                     "source_domain", "language", "author", "publish_date",
                     "canonical_url", "content_hash", mode="before")
    @classmethod
    def coerce_str(cls, v):
        if v is None:
            return ""
        return str(v).strip()

    def to_mongo_dict(self) -> dict:
        """Serialise to MongoDB-ready dict with ISO timestamp."""
        d = self.model_dump()
        d["timestamp"] = self.timestamp.isoformat()
        d["headings"]  = self.headings.model_dump()
        return d

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ─── Quality Gate ─────────────────────────────────────────────────────────────

class QualityGate:
    """
    Pre-storage validation layer.
    Raises ValueError with rejection reason if document fails quality checks.
    """
    MIN_WORD_COUNT      = 120
    MIN_RELEVANCE       = 0.40
    MIN_SUMMARY_LENGTH  = 30
    MIN_KEY_POINTS      = 1

    @classmethod
    def validate(cls, doc: ProcessedContent) -> None:
        errors = []

        if doc.word_count < cls.MIN_WORD_COUNT:
            errors.append(f"word_count={doc.word_count} < {cls.MIN_WORD_COUNT}")

        if doc.relevance_score < cls.MIN_RELEVANCE:
            errors.append(f"relevance={doc.relevance_score:.3f} < {cls.MIN_RELEVANCE}")

        if not doc.clean_text or len(doc.clean_text.strip()) < 100:
            errors.append("empty_or_near_empty_clean_text")

        if not doc.content_summary or len(doc.content_summary) < cls.MIN_SUMMARY_LENGTH:
            errors.append(f"summary_too_short:{len(doc.content_summary)}_chars")

        if len(doc.key_points) < cls.MIN_KEY_POINTS:
            errors.append("no_key_points_extracted")

        if not doc.content_hash:
            errors.append("missing_content_hash")

        if errors:
            raise ValueError("quality_gate_rejected:" + "|".join(errors))

        # Soft warnings (logged but not rejected)
        if doc.confidence_score < 0.3:
            pass  # low confidence but still stored


# ─── API Schemas ─────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query:         str = Field(..., min_length=2, max_length=500)
    max_results:   int = Field(default=30, ge=1, le=50)
    search_engine: str = Field(default="auto")

class SearchResponse(BaseModel):
    job_id:     str
    query:      str
    urls_found: int
    queued:     int
    message:    str

class JobStatus(BaseModel):
    job_id:       str
    query:        str
    total_urls:   int
    pending:      int
    processing:   int
    completed:    int
    failed:       int
    skipped:      int
    progress_pct: float

class ContentQuery(BaseModel):
    query:         str
    min_relevance: float = 0.40
    limit:         int   = 20
    skip:          int   = 0
