import uuid
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.storage.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    subscriber_id: Mapped[str] = mapped_column(String(200), nullable=False)
    subscriber_type: Mapped[str] = mapped_column(String(50), default="email")

    subscription_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[str] = mapped_column(String(500), nullable=False)

    channels: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), default=["email"]
    )
    frequency: Mapped[str] = mapped_column(String(20), default="daily")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "subscriber_id",
            "subscription_type",
            "target_value",
            name="uq_subscription",
        ),
    )


class ApiRateLimit(Base):
    __tablename__ = "api_rate_limits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    api_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    requests_remaining: Mapped[int | None] = mapped_column(Integer)
    requests_limit: Mapped[int | None] = mapped_column(Integer)
    reset_at: Mapped[datetime | None] = mapped_column()

    requests_today: Mapped[int] = mapped_column(Integer, default=0)
    last_request_at: Mapped[datetime | None] = mapped_column()

    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )
