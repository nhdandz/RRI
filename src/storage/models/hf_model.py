import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.storage.database import Base


class HFModel(Base):
    __tablename__ = "hf_models"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    model_id: Mapped[str] = mapped_column(
        String(300), unique=True, nullable=False, index=True
    )
    author: Mapped[str | None] = mapped_column(String(150))
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    pipeline_tag: Mapped[str | None] = mapped_column(String(100))
    architecture: Mapped[str | None] = mapped_column(String(200))
    model_type: Mapped[str | None] = mapped_column(String(100))
    library_name: Mapped[str | None] = mapped_column(String(100))
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(200)))
    languages: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)))
    license: Mapped[str | None] = mapped_column(String(100))
    parameter_count: Mapped[int | None] = mapped_column(BigInteger)

    created_at_hf: Mapped[datetime | None] = mapped_column(DateTime)
    last_modified_hf: Mapped[datetime | None] = mapped_column(DateTime)

    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_hf_models_downloads", "downloads", postgresql_using="btree"),
        Index("idx_hf_models_likes", "likes", postgresql_using="btree"),
        Index("idx_hf_models_pipeline_tag", "pipeline_tag"),
        Index("idx_hf_models_tags", "tags", postgresql_using="gin"),
    )
