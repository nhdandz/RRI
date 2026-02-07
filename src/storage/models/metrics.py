import uuid
from datetime import date, datetime

from sqlalchemy import Date, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.storage.database import Base


class MetricsHistory(Base):
    __tablename__ = "metrics_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Metrics snapshot
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Calculated velocities
    velocity_1d: Mapped[float | None] = mapped_column(Float)
    velocity_7d: Mapped[float | None] = mapped_column(Float)
    velocity_30d: Mapped[float | None] = mapped_column(Float)

    recorded_at: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "recorded_at", name="uq_metrics_entity_date"),
        Index("idx_metrics_entity", "entity_type", "entity_id"),
        Index("idx_metrics_date", "recorded_at"),
    )


class TrendingScore(Base):
    __tablename__ = "trending_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Component scores
    activity_score: Mapped[float] = mapped_column(Float, default=0)
    community_score: Mapped[float] = mapped_column(Float, default=0)
    academic_score: Mapped[float] = mapped_column(Float, default=0)
    recency_score: Mapped[float] = mapped_column(Float, default=0)

    # Combined score
    total_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Ranking
    category: Mapped[str | None] = mapped_column(String(100))
    rank_in_category: Mapped[int | None] = mapped_column(Integer)

    # Time period
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    calculated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "entity_type", "entity_id", "period_start", name="uq_trending_entity_period"
        ),
        Index("idx_trending_score", "total_score"),
        Index("idx_trending_category", "category", "rank_in_category"),
    )


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    source: Mapped[str] = mapped_column(String(50), nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Progress
    total_items: Mapped[int | None] = mapped_column(Integer)
    processed_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()

    # Error tracking
    last_error: Mapped[str | None] = mapped_column(Text)
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    # Parameters
    params: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_crawl_jobs_source", "source", "status"),
    )
