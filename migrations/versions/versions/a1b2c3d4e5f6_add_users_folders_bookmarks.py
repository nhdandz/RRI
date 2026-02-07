"""add users folders bookmarks

Revision ID: a1b2c3d4e5f6
Revises: 452061ad82dc
Create Date: 2026-02-07 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '452061ad82dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Folders table
    op.create_table('folders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'parent_id', 'name', name='uq_folder_user_parent_name'),
    )
    op.create_index('ix_folders_user_id', 'folders', ['user_id'])

    # Bookmarks table
    op.create_table('bookmarks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('folder_id', sa.UUID(), nullable=False),
        sa.Column('item_type', sa.String(length=20), nullable=False),
        sa.Column('item_id', sa.UUID(), nullable=True),
        sa.Column('external_url', sa.Text(), nullable=True),
        sa.Column('external_title', sa.String(length=500), nullable=True),
        sa.Column('external_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'folder_id', 'item_type', 'item_id', name='uq_bookmark_user_folder_item'),
    )
    op.create_index('ix_bookmarks_user_id', 'bookmarks', ['user_id'])
    op.create_index('ix_bookmarks_folder_id', 'bookmarks', ['folder_id'])


def downgrade() -> None:
    op.drop_table('bookmarks')
    op.drop_table('folders')
    op.drop_table('users')
