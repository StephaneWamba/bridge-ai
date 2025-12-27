"""Service for managing integrations."""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.integration import Integration
from src.models.user import User
from src.core.security import encrypt_token, decrypt_token
from src.integrations.hubspot.oauth import HubSpotOAuth
from src.integrations.hubspot.client import HubSpotClient


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
        """Get integration for a user and provider."""
        from uuid import UUID

        result = await db.execute(
            select(Integration)
            .where(Integration.user_id == UUID(user_id))
            .where(Integration.provider == provider)
        )
        return result.scalar_one_or_none()

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
        return integration

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
