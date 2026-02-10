"""add community_posts, github_discussions, openreview_notes

Revision ID: c8a9b0d1e2f3
Revises: b35dadd51d6a
Create Date: 2026-02-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c8a9b0d1e2f3'
down_revision: Union[str, None] = 'b35dadd51d6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # community_posts
    op.create_table(
        'community_posts',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('external_id', sa.String(200), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('author', sa.String(200), nullable=True),
        sa.Column('author_url', sa.Text(), nullable=True),
        sa.Column('score', sa.Integer(), server_default='0'),
        sa.Column('comments_count', sa.Integer(), server_default='0'),
        sa.Column('shares_count', sa.Integer(), server_default='0'),
        sa.Column('tags', postgresql.ARRAY(sa.String(200)), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('extra', postgresql.JSONB(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('collected_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('uq_community_platform_external', 'community_posts', ['platform', 'external_id'], unique=True)
    op.create_index('idx_community_platform', 'community_posts', ['platform'])
    op.create_index('idx_community_score', 'community_posts', ['score'])
    op.create_index('idx_community_published_at', 'community_posts', ['published_at'])
    op.create_index('idx_community_tags', 'community_posts', ['tags'], postgresql_using='gin')

    # github_discussions
    op.create_table(
        'github_discussions',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('discussion_id', sa.String(100), nullable=False, unique=True),
        sa.Column('repo_full_name', sa.String(300), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('author', sa.String(150), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('labels', postgresql.ARRAY(sa.String(200)), nullable=True),
        sa.Column('upvotes', sa.Integer(), server_default='0'),
        sa.Column('comments_count', sa.Integer(), server_default='0'),
        sa.Column('answer_chosen', sa.Boolean(), server_default='false'),
        sa.Column('top_comments', postgresql.JSONB(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('collected_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_gh_discussion_repo', 'github_discussions', ['repo_full_name'])
    op.create_index('idx_gh_discussion_upvotes', 'github_discussions', ['upvotes'])
    op.create_index('idx_gh_discussion_category', 'github_discussions', ['category'])
    op.create_index('idx_gh_discussion_published_at', 'github_discussions', ['published_at'])
    op.create_index('idx_gh_discussion_labels', 'github_discussions', ['labels'], postgresql_using='gin')

    # openreview_notes
    op.create_table(
        'openreview_notes',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('note_id', sa.String(200), nullable=False, unique=True),
        sa.Column('forum_id', sa.String(200), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('authors', postgresql.ARRAY(sa.String(300)), nullable=True),
        sa.Column('venue', sa.String(200), nullable=True),
        sa.Column('venueid', sa.String(200), nullable=True),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('review_count', sa.Integer(), server_default='0'),
        sa.Column('ratings', postgresql.JSONB(), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String(200)), nullable=True),
        sa.Column('pdf_url', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('collected_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_openreview_forum', 'openreview_notes', ['forum_id'])
    op.create_index('idx_openreview_venue', 'openreview_notes', ['venue'])
    op.create_index('idx_openreview_avg_rating', 'openreview_notes', ['average_rating'])
    op.create_index('idx_openreview_published_at', 'openreview_notes', ['published_at'])
    op.create_index('idx_openreview_keywords', 'openreview_notes', ['keywords'], postgresql_using='gin')


def downgrade() -> None:
    op.drop_table('openreview_notes')
    op.drop_table('github_discussions')
    op.drop_table('community_posts')
