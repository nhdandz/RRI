import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.storage.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Identifiers
    arxiv_id: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    doi: Mapped[str | None] = mapped_column(String(100), unique=True)
    semantic_scholar_id: Mapped[str | None] = mapped_column(String(50), index=True)

    # Basic info
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_normalized: Mapped[str | None] = mapped_column(String(500))
    abstract: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)

    # Authors (JSONB array)
    authors: Mapped[dict | None] = mapped_column(JSONB, default=list)

    # Classification
    categories: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)))
    topics: Mapped[list[str] | None] = mapped_column(ARRAY(String(100)))
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String(100)))

    # Dates
    published_date: Mapped[date | None] = mapped_column(Date)
    updated_date: Mapped[date | None] = mapped_column(Date)

    # Source
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    pdf_url: Mapped[str | None] = mapped_column(Text)

    # Metrics
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    influential_citation_count: Mapped[int] = mapped_column(Integer, default=0)

    # Processing status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_relevant: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float)

    # Vietnamese specific
    is_vietnamese: Mapped[bool] = mapped_column(Boolean, default=False)
    vietnam_entities: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_papers_published_date", "published_date", postgresql_using="btree"),
        Index("idx_papers_categories", "categories", postgresql_using="gin"),
        Index("idx_papers_topics", "topics", postgresql_using="gin"),
    )
