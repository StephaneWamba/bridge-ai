"""Integration endpoints for OAuth and API access."""

import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_database_session
from src.integrations.hubspot.oauth import HubSpotOAuth
from src.services.integration_service import IntegrationService
from src.services.oauth_state_service import OAuthStateService
from src.core.config import settings
from src.core.logging import logger

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.get("/hubspot/authorize")
async def hubspot_authorize(
    db: AsyncSession = Depends(get_database_session),
):
    """Initiate HubSpot OAuth flow."""
    # For now, we'll use a default user_id (single-user system)
    # In production, this would come from authentication
    user_id = "00000000-0000-0000-0000-000000000000"  # Default user

    oauth = HubSpotOAuth()
    state = secrets.token_urlsafe(32)

    # Store state in database for CSRF protection
    await OAuthStateService.create_state(
        db=db,
        state=state,
        provider="hubspot",
        user_id=user_id,
    )

    authorization_url = oauth.get_authorization_url(state=state)

    return {"authorization_url": authorization_url, "state": state}


@router.get("/hubspot/callback")
async def hubspot_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_database_session),
):
    """Handle HubSpot OAuth callback."""
    # For now, we'll use a default user_id (single-user system)
    user_id = "00000000-0000-0000-0000-000000000000"  # Default user

    # Verify OAuth state for CSRF protection
    if not state:
        logger.warning("HubSpot OAuth callback missing state parameter")
        frontend_url = "http://localhost:3004"
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
            frontend_url = settings.CORS_ORIGINS[0]
        return RedirectResponse(
            url=f"{frontend_url}/integrations?error=Missing state parameter"
        )

    is_valid = await OAuthStateService.verify_and_delete_state(
        db=db,
        state=state,
        provider="hubspot",
    )

    if not is_valid:
        logger.warning(
            f"HubSpot OAuth callback invalid or expired state: {state}")
        frontend_url = "http://localhost:3004"
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
            frontend_url = settings.CORS_ORIGINS[0]
        return RedirectResponse(
            url=f"{frontend_url}/integrations?error=Invalid or expired state parameter"
        )

    try:
        oauth = HubSpotOAuth()
        token = await oauth.get_token(code)

        # Store integration
        integration = await IntegrationService.create_or_update_integration(
            db=db,
            user_id=user_id,
            provider="hubspot",
            access_token=token["access_token"],
            refresh_token=token.get("refresh_token"),
            expires_in=token.get("expires_in"),
            scope=token.get("scope"),
        )

        # Redirect to frontend success page
        frontend_url = "http://localhost:3004"
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
            frontend_url = settings.CORS_ORIGINS[0]
        return RedirectResponse(
            url=f"{frontend_url}/integrations?success=hubspot"
        )
    except Exception as e:
        # Log the error for debugging
        logger.error(f"HubSpot OAuth callback error: {e}", exc_info=True)

        # Redirect to frontend error page
        frontend_url = "http://localhost:3004"
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
            frontend_url = settings.CORS_ORIGINS[0]

        # URL encode the error message
        from urllib.parse import quote
        error_msg = quote(str(e))
        return RedirectResponse(
            url=f"{frontend_url}/integrations?error={error_msg}"
        )


@router.get("/hubspot/status")
async def hubspot_status(
    db: AsyncSession = Depends(get_database_session),
):
    """Get HubSpot integration status."""
    user_id = "00000000-0000-0000-0000-000000000000"  # Default user

    integration = await IntegrationService.get_integration(db, user_id, "hubspot")

    if not integration:
        return {"connected": False}

    # Test connection
    client = await IntegrationService.get_hubspot_client(db, user_id)
    if client:
        is_working = await client.test_connection()
        return {
            "connected": True,
            "is_active": integration.is_active,
            "expires_at": integration.expires_at.isoformat() if integration.expires_at else None,
            "working": is_working,
        }

    return {"connected": True, "is_active": False}


@router.post("/hubspot/disconnect")
async def hubspot_disconnect(
    db: AsyncSession = Depends(get_database_session),
):
    """Disconnect HubSpot integration."""
    user_id = "00000000-0000-0000-0000-000000000000"  # Default user

    integration = await IntegrationService.get_integration(db, user_id, "hubspot")
    if integration:
        await db.delete(integration)
        await db.commit()

    return {"success": True}
