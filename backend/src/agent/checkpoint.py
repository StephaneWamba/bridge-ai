"""LangGraph checkpoint configuration."""

from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.core.config import settings


@asynccontextmanager
async def get_checkpointer():
    """Get LangGraph PostgreSQL checkpointer (async context manager)."""
    # AsyncPostgresSaver uses psycopg (async), not asyncpg
    # Convert asyncpg URL to psycopg format
    db_url = settings.LANGRAPH_CHECKPOINT_DB_URL.replace("+asyncpg", "")

    # Create and enter the async checkpointer context manager
    async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:
        # Setup tables - this creates the checkpoints table if it doesn't exist
        await checkpointer.setup()
        yield checkpointer
