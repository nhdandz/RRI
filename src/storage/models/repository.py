import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.storage.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Identifiers
    github_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    full_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    readme_content: Mapped[str | None] = mapped_column(Text)
    readme_summary: Mapped[str | None] = mapped_column(Text)

    # URLs
    html_url: Mapped[str] = mapped_column(Text, nullable=False)
    clone_url: Mapped[str | None] = mapped_column(Text)
    homepage_url: Mapped[str | None] = mapped_column(Text)

    # Tech stack
    primary_language: Mapped[str | None] = mapped_column(String(50))
    languages: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    topics: Mapped[list[str] | None] = mapped_column(ARRAY(String(100)))

    # Dependencies
    dependencies: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    frameworks: Mapped[list[str] | None] = mapped_column(ARRAY(String(100)))

    # Metrics
    stars_count: Mapped[int] = mapped_column(Integer, default=0)
    forks_count: Mapped[int] = mapped_column(Integer, default=0)
    watchers_count: Mapped[int] = mapped_column(Integer, default=0)
    open_issues_count: Mapped[int] = mapped_column(Integer, default=0)

    # Activity
    last_commit_at: Mapped[datetime | None] = mapped_column()
    last_release_at: Mapped[datetime | None] = mapped_column()
    last_release_tag: Mapped[str | None] = mapped_column(String(50))
    commit_count_30d: Mapped[int] = mapped_column(Integer, default=0)

    # Quality indicators
    has_readme: Mapped[bool] = mapped_column(Boolean, default=False)
    has_license: Mapped[bool] = mapped_column(Boolean, default=False)
    has_tests: Mapped[bool] = mapped_column(Boolean, default=False)
    has_docker: Mapped[bool] = mapped_column(Boolean, default=False)
    has_ci: Mapped[bool] = mapped_column(Boolean, default=False)

    # Processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )
    repo_created_at: Mapped[datetime | None] = mapped_column()
    repo_updated_at: Mapped[datetime | None] = mapped_column()

    __table_args__ = (
        Index("idx_repos_stars", "stars_count", postgresql_using="btree"),
        Index("idx_repos_language", "primary_language"),
        Index("idx_repos_topics", "topics", postgresql_using="gin"),
        Index("idx_repos_frameworks", "frameworks", postgresql_using="gin"),
    )
