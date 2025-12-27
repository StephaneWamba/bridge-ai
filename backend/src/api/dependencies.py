"""FastAPI dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db


async def get_database_session(
    session: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """Dependency for database session."""
    return session

