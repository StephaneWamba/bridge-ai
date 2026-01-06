"""Integration endpoints for OAuth and API access."""

import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_database_session, get_current_user
from src.models.user import User
from src.integrations.hubspot.oauth import HubSpotOAuth
from src.integrations.gmail.oauth import GoogleOAuth
from src.services.integration_service import IntegrationService
from src.services.oauth_state_service import OAuthStateService
from src.core.config import settings
from src.core.logging import logger

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.get("/hubspot/authorize")
async def hubspot_authorize(
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """Initiate HubSpot OAuth flow."""
    user_id = str(current_user.id)

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
    # Verify OAuth state for CSRF protection
    if not state:
        logger.warning("HubSpot OAuth callback missing state parameter")
        frontend_url = "http://localhost:3004"
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
            frontend_url = settings.CORS_ORIGINS[0]
        return RedirectResponse(
            url=f"{frontend_url}/integrations?error=Missing state parameter"
        )

    # Get user_id from OAuth state
    oauth_state = await OAuthStateService.get_state(db=db, state=state, provider="hubspot")
    if not oauth_state:
        frontend_url = "http://localhost:3004"
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
            frontend_url = settings.CORS_ORIGINS[0]
        return RedirectResponse(
            url=f"{frontend_url}/integrations?error=Invalid or expired state parameter"
        )
    
    user_id = str(oauth_state.user_id)
    
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
    current_user: User = Depends(get_current_user),
):
    """Get HubSpot integration status."""
    user_id = str(current_user.id)

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
    current_user: User = Depends(get_current_user),
):
    """Disconnect HubSpot integration."""
    user_id = str(current_user.id)

    try:
        deleted = await IntegrationService.delete_integration(db, user_id, "hubspot")
        return {
            "success": True, 
            "message": "HubSpot integration disconnected",
            "deleted": deleted
        }
    except Exception as e:
        logger.error(f"Error disconnecting HubSpot integration: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error disconnecting HubSpot: {str(e)}"
        )


# Google OAuth (Gmail + Calendar)
@router.get("/google/authorize")
async def google_authorize(
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """Initiate Google OAuth flow (Gmail + Calendar)."""
    user_id = str(current_user.id)

    oauth = GoogleOAuth()
    state = secrets.token_urlsafe(32)

    # Store state in database for CSRF protection
    await OAuthStateService.create_state(
        db=db,
        state=state,
        provider="google",
        user_id=user_id,
    )

    authorization_url = oauth.get_authorization_url(state=state)

    return {"authorization_url": authorization_url, "state": state}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_database_session),
):
    """Handle Google OAuth callback (Gmail + Calendar)."""
    # Verify OAuth state for CSRF protection
    if not state:
        logger.warning("Google OAuth callback missing state parameter")
        frontend_url = "http://localhost:3004"
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
            frontend_url = settings.CORS_ORIGINS[0]
        return RedirectResponse(
            url=f"{frontend_url}/integrations?error=Missing state parameter"
        )

    # Get user_id from OAuth state
    oauth_state = await OAuthStateService.get_state(db=db, state=state, provider="google")
    if not oauth_state:
        frontend_url = "http://localhost:3004"
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
            frontend_url = settings.CORS_ORIGINS[0]
        return RedirectResponse(
            url=f"{frontend_url}/integrations?error=Invalid or expired state parameter"
        )
    
    user_id = str(oauth_state.user_id)
    
    is_valid = await OAuthStateService.verify_and_delete_state(
        db=db,
        state=state,
        provider="google",
    )

    if not is_valid:
        logger.warning(
            f"Google OAuth callback invalid or expired state: {state}")
        frontend_url = "http://localhost:3004"
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
            frontend_url = settings.CORS_ORIGINS[0]
        return RedirectResponse(
            url=f"{frontend_url}/integrations?error=Invalid or expired state parameter"
        )

    try:
        oauth = GoogleOAuth()
        token = await oauth.get_token(code)

        # Calculate expires_in from expires_at if available
        expires_in = None
        if token.get("expires_at"):
            from datetime import datetime
            expires_at = datetime.fromisoformat(
                token["expires_at"].replace("Z", "+00:00"))
            expires_in = int((expires_at - datetime.utcnow()).total_seconds())

        # Store integration for Gmail (provider: "gmail")
        integration = await IntegrationService.create_or_update_integration(
            db=db,
            user_id=user_id,
            provider="gmail",
            access_token=token["access_token"],
            refresh_token=token.get("refresh_token"),
            expires_in=expires_in,
            scope=" ".join(token.get("scope", [])),
        )

        # Also store for Calendar (provider: "calendar") - same tokens
        await IntegrationService.create_or_update_integration(
            db=db,
            user_id=user_id,
            provider="calendar",
            access_token=token["access_token"],
            refresh_token=token.get("refresh_token"),
            expires_in=expires_in,
            scope=" ".join(token.get("scope", [])),
        )

        # Redirect to frontend success page
        frontend_url = "http://localhost:3004"
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
            frontend_url = settings.CORS_ORIGINS[0]
        return RedirectResponse(
            url=f"{frontend_url}/integrations?success=google"
        )
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}", exc_info=True)

        frontend_url = "http://localhost:3004"
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != ["*"]:
            frontend_url = settings.CORS_ORIGINS[0]

        from urllib.parse import quote
        error_msg = quote(str(e))
        return RedirectResponse(
            url=f"{frontend_url}/integrations?error={error_msg}"
        )


@router.get("/google/status")
async def google_status(
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """Get Google integration status (Gmail + Calendar)."""
    user_id = str(current_user.id)

    gmail_integration = await IntegrationService.get_integration(db, user_id, "gmail")
    calendar_integration = await IntegrationService.get_integration(db, user_id, "calendar")

    return {
        "gmail": {
            "connected": gmail_integration is not None and gmail_integration.is_active,
            "is_active": gmail_integration.is_active if gmail_integration else False,
        },
        "calendar": {
            "connected": calendar_integration is not None and calendar_integration.is_active,
            "is_active": calendar_integration.is_active if calendar_integration else False,
        },
    }


@router.post("/google/disconnect")
async def google_disconnect(
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """Disconnect Google integration (Gmail + Calendar + Drive)."""
    user_id = str(current_user.id)

    try:
        # Delete both Gmail and Calendar integrations (they share tokens)
        gmail_deleted = await IntegrationService.delete_integration(db, user_id, "gmail")
        calendar_deleted = await IntegrationService.delete_integration(db, user_id, "calendar")
        
        deleted_count = sum([gmail_deleted, calendar_deleted])
        
        return {
            "success": True, 
            "message": "Google integration disconnected",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error disconnecting Google integration: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error disconnecting Google: {str(e)}"
        )
