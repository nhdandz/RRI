import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.storage.database import Base


class PaperRepoLink(Base):
    __tablename__ = "paper_repo_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False
    )
    repo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Link metadata
    link_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Evidence
    evidence: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Source of discovery
    discovered_via: Mapped[str | None] = mapped_column(String(50))

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime | None] = mapped_column()
    verified_by: Mapped[str | None] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("paper_id", "repo_id", name="uq_paper_repo"),
    )
