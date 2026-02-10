import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.storage.database import Base


class OpenReviewNote(Base):
    __tablename__ = "openreview_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    note_id: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False, index=True
    )
    forum_id: Mapped[str | None] = mapped_column(String(200), index=True)
    title: Mapped[str | None] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    tldr: Mapped[str | None] = mapped_column(Text)
    authors: Mapped[list[str] | None] = mapped_column(ARRAY(String(300)))
    venue: Mapped[str | None] = mapped_column(String(200))
    venueid: Mapped[str | None] = mapped_column(String(200))
    primary_area: Mapped[str | None] = mapped_column(String(300))
    average_rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    reviews_fetched: Mapped[bool] = mapped_column(Boolean, default=False)
    ratings: Mapped[dict | None] = mapped_column(JSONB)
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String(200)))
    pdf_url: Mapped[str | None] = mapped_column(Text)

    paper_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="SET NULL"), index=True
    )

    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_openreview_venue", "venue"),
        Index("idx_openreview_venueid", "venueid"),
        Index("idx_openreview_avg_rating", "average_rating", postgresql_using="btree"),
        Index("idx_openreview_published_at", "published_at"),
        Index("idx_openreview_keywords", "keywords", postgresql_using="gin"),
        Index("idx_openreview_primary_area", "primary_area"),
        Index("idx_openreview_paper_id", "paper_id"),
    )
