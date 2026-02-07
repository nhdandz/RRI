import uuid
from datetime import datetime

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.storage.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Related entities
    entity_type: Mapped[str | None] = mapped_column(String(20))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Alert content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="info")

    # Additional data
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)

    # Status
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime | None] = mapped_column()
    sent_channels: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)))

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_alerts_type", "alert_type"),
        Index("idx_alerts_created", "created_at"),
    )
