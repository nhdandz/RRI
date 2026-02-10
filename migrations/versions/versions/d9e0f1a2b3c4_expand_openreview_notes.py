"""Expand openreview_notes with paper_id, primary_area, tldr, reviews_fetched

Revision ID: d9e0f1a2b3c4
Revises: c8a9b0d1e2f3
Create Date: 2026-02-10 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "d9e0f1a2b3c4"
down_revision = "c8a9b0d1e2f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("openreview_notes", sa.Column("tldr", sa.Text(), nullable=True))
    op.add_column("openreview_notes", sa.Column("primary_area", sa.String(300), nullable=True))
    op.add_column("openreview_notes", sa.Column("reviews_fetched", sa.Boolean(), server_default="false", nullable=False))
    op.add_column(
        "openreview_notes",
        sa.Column("paper_id", UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="SET NULL"), nullable=True),
    )

    op.create_index("idx_openreview_venueid", "openreview_notes", ["venueid"])
    op.create_index("idx_openreview_primary_area", "openreview_notes", ["primary_area"])
    op.create_index("idx_openreview_paper_id", "openreview_notes", ["paper_id"])


def downgrade() -> None:
    op.drop_index("idx_openreview_paper_id", table_name="openreview_notes")
    op.drop_index("idx_openreview_primary_area", table_name="openreview_notes")
    op.drop_index("idx_openreview_venueid", table_name="openreview_notes")
    op.drop_column("openreview_notes", "paper_id")
    op.drop_column("openreview_notes", "reviews_fetched")
    op.drop_column("openreview_notes", "primary_area")
    op.drop_column("openreview_notes", "tldr")
