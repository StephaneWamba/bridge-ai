"""Service for managing integrations."""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.integration import Integration
from src.models.user import User
from src.core.security import encrypt_token, decrypt_token
from src.core.cache import get_cache, cache_key
from src.core.logging import logger
from src.integrations.hubspot.oauth import HubSpotOAuth
from src.integrations.hubspot.client import HubSpotClient
from src.integrations.gmail.oauth import GoogleOAuth
from src.integrations.gmail.client import GmailClient
from src.integrations.calendar.client import CalendarClient
from src.integrations.discord.client import DiscordClient
from src.integrations.drive.client import DriveClient
from src.core.config import settings


class IntegrationService:
    """Service for managing user integrations."""

    @staticmethod
    async def get_or_create_default_user(db: AsyncSession, user_id: str) -> User:
        """Get or create the default user for single-user system."""
        from uuid import UUID

        user_uuid = UUID(user_id)
        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=user_uuid,
                email="default@bridgeai.local",
                is_active=True,
            )
            db.add(user)
            await db.flush()  # Flush to get the user ID

        return user

    @staticmethod
    async def get_integration(
        db: AsyncSession, user_id: str, provider: str
    ) -> Optional[Integration]:
        """Get integration for a user and provider (with caching)."""
        from uuid import UUID
        cache = get_cache()
        cache_key_str = cache_key("integration", user_id, provider)

        # Try cache first
        cached = cache.get(cache_key_str)
        if cached is not None:
            return cached

        # Query database
        result = await db.execute(
            select(Integration)
            .where(Integration.user_id == UUID(user_id))
            .where(Integration.provider == provider)
        )
        integration = result.scalar_one_or_none()

        # Cache for 5 minutes (integration changes are infrequent)
        if integration is not None:
            cache.set(cache_key_str, integration, ttl_seconds=300)

        return integration

    @staticmethod
    async def create_or_update_integration(
        db: AsyncSession,
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_in: Optional[int] = None,
        scope: Optional[str] = None,
    ) -> Integration:
        """Create or update an integration."""
        from uuid import UUID

        # Ensure user exists first
        await IntegrationService.get_or_create_default_user(db, user_id)

        integration = await IntegrationService.get_integration(db, user_id, provider)

        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        if integration:
            # Update existing
            integration.access_token = encrypt_token(access_token)
            if refresh_token:
                integration.refresh_token = encrypt_token(refresh_token)
            integration.expires_at = expires_at
            if scope:
                integration.scope = scope
            integration.updated_at = datetime.utcnow()
        else:
            # Create new
            integration = Integration(
                user_id=UUID(user_id),
                provider=provider,
                access_token=encrypt_token(access_token),
                refresh_token=encrypt_token(
                    refresh_token) if refresh_token else None,
                expires_at=expires_at,
                scope=scope,
            )
            db.add(integration)

        await db.commit()
        await db.refresh(integration)

        # Invalidate cache for this integration
        cache = get_cache()
        cache_key_str = cache_key("integration", user_id, provider)
        cache.delete(cache_key_str)

        return integration

    @staticmethod
    async def delete_integration(
        db: AsyncSession, user_id: str, provider: str
    ) -> bool:
        """Delete an integration and clear cache."""
        from uuid import UUID
        from sqlalchemy import delete

        # First, invalidate cache
        cache = get_cache()
        cache_key_str = cache_key("integration", user_id, provider)
        cache.delete(cache_key_str)

        # Delete from database
        stmt = (
            delete(Integration)
            .where(Integration.user_id == UUID(user_id))
            .where(Integration.provider == provider)
        )
        result = await db.execute(stmt)
        await db.commit()

        if result.rowcount > 0:
            logger.info(f"Integration {provider} deleted for user {user_id}")
            return True

        logger.warning(f"Integration {provider} not found for user {user_id}")
        return False

    @staticmethod
    async def get_hubspot_client(
        db: AsyncSession, user_id: str
    ) -> Optional[HubSpotClient]:
        """Get HubSpot client for a user with automatic DB sync on token refresh."""
        integration = await IntegrationService.get_integration(db, user_id, "hubspot")
        if not integration:
            return None

        access_token = decrypt_token(integration.access_token)
        refresh_token = (
            decrypt_token(
                integration.refresh_token) if integration.refresh_token else None
        )

        # Create callback to update DB when token is refreshed
        async def on_token_refresh(
            new_access_token: str,
            new_refresh_token: Optional[str],
            expires_in: Optional[int],
        ):
            """Update integration in DB when token is refreshed."""
            await IntegrationService.create_or_update_integration(
                db=db,
                user_id=user_id,
                provider="hubspot",
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=expires_in,
                scope=integration.scope,
            )

        return HubSpotClient(
            access_token=access_token,
            refresh_token=refresh_token,
            on_token_refresh=on_token_refresh,
        )

    @staticmethod
    async def refresh_integration_token(
        db: AsyncSession, user_id: str, provider: str
    ) -> Optional[Integration]:
        """Refresh integration token if expired."""
        integration = await IntegrationService.get_integration(db, user_id, provider)
        if not integration or not integration.refresh_token:
            return None

        if provider == "hubspot":
            oauth = HubSpotOAuth()
            refresh_token = decrypt_token(integration.refresh_token)
            token = await oauth.refresh_token(refresh_token)

            expires_in = token.get("expires_in")
            return await IntegrationService.create_or_update_integration(
                db=db,
                user_id=user_id,
                provider=provider,
                access_token=token["access_token"],
                refresh_token=token.get("refresh_token"),
                expires_in=expires_in,
                scope=integration.scope,
            )

        return None

    @staticmethod
    async def get_google_client(
        db: AsyncSession, user_id: str
    ) -> Optional[GmailClient]:
        """Get Google (Gmail) client for a user with automatic DB sync on token refresh."""
        integration = await IntegrationService.get_integration(db, user_id, "gmail")
        if not integration:
            return None

        access_token = decrypt_token(integration.access_token)
        refresh_token = (
            decrypt_token(
                integration.refresh_token) if integration.refresh_token else None
        )

        # Create callback to update DB when token is refreshed
        async def on_token_refresh(
            new_access_token: str,
            new_refresh_token: Optional[str],
            expires_in: Optional[int],
        ):
            """Update integration in DB when token is refreshed."""
            await IntegrationService.create_or_update_integration(
                db=db,
                user_id=user_id,
                provider="gmail",
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=expires_in,
                scope=integration.scope,
            )

        return GmailClient(
            access_token=access_token,
            refresh_token=refresh_token,
            on_token_refresh=on_token_refresh,
        )

    @staticmethod
    async def get_calendar_client(
        db: AsyncSession, user_id: str
    ) -> Optional[CalendarClient]:
        """Get Calendar client for a user with automatic DB sync on token refresh.

        Calendar uses the same Google OAuth tokens as Gmail, so we fetch the 'gmail' integration.
        The Google OAuth flow should request both Gmail and Calendar scopes.
        """
        # Calendar uses the same Google OAuth tokens as Gmail (stored under "gmail" provider)
        integration = await IntegrationService.get_integration(db, user_id, "gmail")
        if not integration:
            return None

        access_token = decrypt_token(integration.access_token)
        refresh_token = (
            decrypt_token(
                integration.refresh_token) if integration.refresh_token else None
        )

        # Create callback to update DB when token is refreshed
        async def on_token_refresh(
            new_access_token: str,
            new_refresh_token: Optional[str],
            expires_in: Optional[int],
        ):
            """Update integration in DB when token is refreshed."""
            await IntegrationService.create_or_update_integration(
                db=db,
                user_id=user_id,
                provider="gmail",  # Update the "gmail" integration as it holds the shared tokens
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=expires_in,
                scope=integration.scope,
            )

        return CalendarClient(
            access_token=access_token,
            refresh_token=refresh_token,
            on_token_refresh=on_token_refresh,
        )

    @staticmethod
    async def get_drive_client(
        db: AsyncSession, user_id: str
    ) -> Optional[DriveClient]:
        """Get Drive client for a user with automatic DB sync on token refresh.

        Drive uses the same Google OAuth tokens as Gmail/Calendar, so we fetch the 'gmail' integration.
        The Google OAuth flow should request Drive scope in addition to Gmail and Calendar scopes.
        """
        # Drive uses the same Google OAuth tokens as Gmail/Calendar (stored under "gmail" provider)
        integration = await IntegrationService.get_integration(db, user_id, "gmail")
        if not integration:
            return None

        access_token = decrypt_token(integration.access_token)
        refresh_token = (
            decrypt_token(
                integration.refresh_token) if integration.refresh_token else None
        )

        # Create callback to update DB when token is refreshed
        async def on_token_refresh(
            new_access_token: str,
            new_refresh_token: Optional[str],
            expires_in: Optional[int],
        ):
            """Update integration in DB when token is refreshed."""
            await IntegrationService.create_or_update_integration(
                db=db,
                user_id=user_id,
                provider="gmail",  # Update the "gmail" integration as it holds the shared tokens
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=expires_in,
                scope=integration.scope,
            )

        return DriveClient(
            access_token=access_token,
            refresh_token=refresh_token,
            on_token_refresh=on_token_refresh,
        )

    @staticmethod
    async def get_discord_client(
        db: AsyncSession, user_id: str
    ) -> Optional[DiscordClient]:
        """Get Discord client for a user.

        Discord bots use static bot tokens (not OAuth per-user tokens).
        The bot token is stored in environment variables and shared across all users.
        The db and user_id parameters are kept for interface consistency but are not used.
        """
        bot_token = settings.DISCORD_BOT_TOKEN

        if not bot_token:
            return None  # No Discord bot token configured

        return DiscordClient(bot_token=bot_token)
