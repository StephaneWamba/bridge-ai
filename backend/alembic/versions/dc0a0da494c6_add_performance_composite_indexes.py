"""add_performance_composite_indexes

Revision ID: dc0a0da494c6
Revises: ee79c6650f3a
Create Date: 2025-12-27 23:09:10.473715

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dc0a0da494c6'
down_revision = '64069ab76828'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add composite index for conversations query pattern: user_id + updated_at (for list_conversations ORDER BY updated_at DESC)
    # This optimizes queries that filter by user_id and order by updated_at
    op.create_index(
        'ix_conversations_user_id_updated_at',
        'conversations',
        ['user_id', 'updated_at'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_conversations_user_id_updated_at', table_name='conversations')

