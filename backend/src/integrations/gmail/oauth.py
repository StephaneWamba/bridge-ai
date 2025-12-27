"""Google OAuth2 implementation for Gmail and Calendar."""

import os
from typing import Optional
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from src.core.config import settings

# Allow insecure transport for localhost development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


class GoogleOAuth:
    """Google OAuth2 client for Gmail and Calendar."""

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/drive.readonly",  # For accessing meeting transcripts
        "https://www.googleapis.com/auth/drive.file",  # For creating/editing files (restricted to files created by the app)
    ]

    def __init__(self):
        """Initialize Google OAuth client."""
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

        # Validate credentials are set
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables")

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate Google OAuth authorization URL."""
        if not self.client_id or not self.client_secret:
            raise ValueError("Google OAuth credentials not configured")

        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri],
            }
        }

        flow = Flow.from_client_config(
            client_config,
            scopes=self.SCOPES,
        )
        flow.redirect_uri = self.redirect_uri

        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="consent",  # Force consent to get refresh token
        )

        return authorization_url

    async def get_token(self, code: str) -> dict:
        """Exchange authorization code for access token."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from urllib.parse import urlencode

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.SCOPES,
        )
        flow.redirect_uri = self.redirect_uri

        # Build the authorization response URL that fetch_token expects
        # fetch_token expects the full redirect URL with code parameter
        auth_response = f"{self.redirect_uri}?code={code}"

        # Run synchronous flow.fetch_token in thread pool
        # fetch_token only accepts keyword arguments, so we need a wrapper
        def fetch_token_wrapper():
            return flow.fetch_token(authorization_response=auth_response)

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, fetch_token_wrapper)

        credentials = flow.credentials

        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expires_in": None,  # Google uses expires_at in credentials
            "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
            "scope": credentials.scopes,
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

        # Run synchronous refresh in thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, credentials.refresh, Request())

        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token or refresh_token,
            "expires_in": None,
            "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
            "scope": credentials.scopes,
        }
