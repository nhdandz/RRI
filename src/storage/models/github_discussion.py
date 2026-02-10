import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.storage.database import Base


class GitHubDiscussion(Base):
    __tablename__ = "github_discussions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    discussion_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    repo_full_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(150))
    category: Mapped[str | None] = mapped_column(String(100))
    labels: Mapped[list[str] | None] = mapped_column(ARRAY(String(200)))
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    answer_chosen: Mapped[bool] = mapped_column(Boolean, default=False)
    top_comments: Mapped[dict | None] = mapped_column(JSONB)

    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_gh_discussion_upvotes", "upvotes", postgresql_using="btree"),
        Index("idx_gh_discussion_category", "category"),
        Index("idx_gh_discussion_published_at", "published_at"),
        Index("idx_gh_discussion_labels", "labels", postgresql_using="gin"),
    )
