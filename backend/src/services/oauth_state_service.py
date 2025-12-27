"""Service for managing OAuth state (CSRF protection)."""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.oauth_state import OAuthState


class OAuthStateService:
    """Service for managing OAuth state tokens."""

    STATE_EXPIRY_MINUTES = 10  # State expires after 10 minutes

    @staticmethod
    async def create_state(
        db: AsyncSession,
        state: str,
        provider: str,
        user_id: str,
    ) -> OAuthState:
        """Create a new OAuth state token."""
        from uuid import UUID

        oauth_state = OAuthState(
            state=state,
            provider=provider,
            user_id=UUID(user_id),
            expires_at=datetime.utcnow() + timedelta(minutes=OAuthStateService.STATE_EXPIRY_MINUTES),
        )
        db.add(oauth_state)
        await db.commit()
        await db.refresh(oauth_state)
        return oauth_state

    @staticmethod
    async def verify_and_delete_state(
        db: AsyncSession,
        state: str,
        provider: str,
    ) -> bool:
        """Verify OAuth state and delete it if valid."""
        stmt = select(OAuthState).where(
            OAuthState.state == state,
            OAuthState.provider == provider,
            OAuthState.expires_at > datetime.utcnow(),
        )
        result = await db.execute(stmt)
        oauth_state = result.scalar_one_or_none()

        if not oauth_state:
            return False

        # Delete the state after verification (one-time use)
        await db.delete(oauth_state)
        await db.commit()
        return True

    @staticmethod
    async def cleanup_expired_states(db: AsyncSession) -> int:
        """Clean up expired OAuth states. Returns number of deleted states."""
        stmt = delete(OAuthState).where(OAuthState.expires_at < datetime.utcnow())
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount or 0

