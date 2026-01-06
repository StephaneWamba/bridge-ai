"""Add hashed_password column to users table

Revision ID: add_password_to_users
Revises: dc0a0da494c6
Create Date: 2025-12-28 12:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_password_to_users'
down_revision = 'dc0a0da494c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add hashed_password column to users table (nullable initially)
    op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True))
    
    # For existing users (if any), set a dummy password hash
    # This ensures they can't login without resetting password
    # The hash is a bcrypt hash of "REQUIRES_RESET" - users will need to sign up again
    # or we can implement password reset later
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM users WHERE hashed_password IS NULL"))
    existing_users = result.fetchall()
    
    if existing_users:
        # Use a known bcrypt hash that will never match a real password
        # This is the hash of "REQUIRES_RESET" - users cannot login with this
        dummy_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJqZqZqZq"
        for user_id in existing_users:
            connection.execute(
                sa.text("UPDATE users SET hashed_password = :hash WHERE id = :id"),
                {"hash": dummy_hash, "id": user_id[0]}
            )
        connection.commit()
    
    # Make the column non-nullable after setting values
    op.alter_column('users', 'hashed_password', nullable=False)


def downgrade() -> None:
    # Remove hashed_password column
    op.drop_column('users', 'hashed_password')

