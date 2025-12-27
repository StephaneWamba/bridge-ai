"""HubSpot OAuth2 implementation using authlib."""

from typing import Optional
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc6749 import OAuth2Token

from src.core.config import settings


class HubSpotOAuth:
    """HubSpot OAuth2 client."""

    def __init__(self):
        """Initialize HubSpot OAuth client."""
        self.client_id = settings.HUBSPOT_CLIENT_ID
        self.client_secret = settings.HUBSPOT_CLIENT_SECRET
        self.redirect_uri = settings.HUBSPOT_REDIRECT_URI
        self.authorize_url = "https://app.hubspot.com/oauth/authorize"
        self.token_url = "https://api.hubapi.com/oauth/v1/token"

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate HubSpot OAuth authorization URL."""
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
        )

        scopes = [
            "crm.objects.contacts.read",
            "crm.objects.contacts.write",
            "crm.objects.companies.read",
            "crm.objects.companies.write",
            "crm.objects.deals.read",
            "crm.objects.deals.write",
        ]
        scope_string = " ".join(scopes)

        authorization_url, _ = client.create_authorization_url(
            self.authorize_url,
            state=state,
            scope=scope_string,
        )

        return authorization_url

    async def get_token(self, code: str) -> dict:
        """Exchange authorization code for access token."""
        import httpx

        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data=data, 
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        import httpx

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()
