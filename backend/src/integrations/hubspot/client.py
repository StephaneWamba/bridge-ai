"""HubSpot API client with rate limiting and error handling."""

import asyncio
from typing import Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from httpx import AsyncClient, HTTPStatusError, Response
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.integrations.base import BaseIntegration
from src.integrations.hubspot.oauth import HubSpotOAuth


class HubSpotRateLimitError(Exception):
    """Raised when HubSpot rate limit is exceeded."""

    pass


class HubSpotAPIError(Exception):
    """Raised when HubSpot API returns an error."""

    pass


class HubSpotClient(BaseIntegration):
    """HubSpot API client with rate limiting and retries."""

    BASE_URL = "https://api.hubapi.com"
    RATE_LIMIT_REQUESTS = 100  # HubSpot free tier: 100 requests per 10 seconds
    RATE_LIMIT_WINDOW = 10  # seconds

    def __init__(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        on_token_refresh: Optional[Callable[[
            str, Optional[str], Optional[int]], Awaitable[None]]] = None,
    ):
        """Initialize HubSpot client.

        Args:
            access_token: HubSpot access token
            refresh_token: HubSpot refresh token (optional)
            on_token_refresh: Optional callback when token is refreshed.
                Should accept (access_token, refresh_token, expires_in) as arguments.
        """
        super().__init__(access_token, refresh_token)
        self.oauth = HubSpotOAuth()
        self._rate_limit_queue: list[datetime] = []
        self._lock = asyncio.Lock()
        self._on_token_refresh = on_token_refresh

    async def _wait_for_rate_limit(self) -> None:
        """Wait if rate limit would be exceeded."""
        async with self._lock:
            now = datetime.utcnow()
            # Remove requests older than the rate limit window
            self._rate_limit_queue = [
                req_time
                for req_time in self._rate_limit_queue
                if (now - req_time).total_seconds() < self.RATE_LIMIT_WINDOW
            ]

            # If we're at the limit, wait until the oldest request expires
            if len(self._rate_limit_queue) >= self.RATE_LIMIT_REQUESTS:
                oldest_request = min(self._rate_limit_queue)
                wait_time = (
                    self.RATE_LIMIT_WINDOW
                    - (now - oldest_request).total_seconds()
                    + 0.1  # Small buffer
                )
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = datetime.utcnow()
                    self._rate_limit_queue = [
                        req_time
                        for req_time in self._rate_limit_queue
                        if (now - req_time).total_seconds() < self.RATE_LIMIT_WINDOW
                    ]

            # Record this request
            self._rate_limit_queue.append(datetime.utcnow())

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make HTTP request to HubSpot API with rate limiting and retries."""
        await self._wait_for_rate_limit()

        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        async with AsyncClient() as client:
            try:
                response: Response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            except HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise HubSpotRateLimitError("HubSpot rate limit exceeded")
                elif e.response.status_code == 401:
                    # Token might be expired, try to refresh
                    if self.refresh_token:
                        await self.refresh_access_token()
                        # Retry the request once with new token
                        headers["Authorization"] = f"Bearer {self.access_token}"
                        response = await client.request(
                            method=method,
                            url=url,
                            headers=headers,
                            params=params,
                            json=json_data,
                            timeout=30.0,
                        )
                        response.raise_for_status()
                        return response.json()
                    raise HubSpotAPIError("Unauthorized - token expired")
                else:
                    error_detail = e.response.text if e.response else "Unknown error"
                    raise HubSpotAPIError(
                        f"HubSpot API error: {e.response.status_code} - {error_detail}"
                    )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (HubSpotRateLimitError, HubSpotAPIError)),
    )
    async def get_contact(self, contact_id: str) -> dict[str, Any]:
        """Get a contact by ID."""
        return await self._make_request("GET", f"/crm/v3/objects/contacts/{contact_id}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (HubSpotRateLimitError, HubSpotAPIError)),
    )
    async def search_contacts(
        self, query: Optional[str] = None, limit: int = 10
    ) -> dict[str, Any]:
        """Search contacts."""
        if query:
            # Use search endpoint for query
            return await self._make_request(
                "POST",
                "/crm/v3/objects/contacts/search",
                json_data={
                    "query": query,
                    "limit": limit,
                },
            )
        else:
            # Use list endpoint for all contacts
            return await self._make_request(
                "GET",
                "/crm/v3/objects/contacts",
                params={"limit": limit},
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (HubSpotRateLimitError, HubSpotAPIError)),
    )
    async def get_company(self, company_id: str) -> dict[str, Any]:
        """Get a company by ID."""
        return await self._make_request("GET", f"/crm/v3/objects/companies/{company_id}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (HubSpotRateLimitError, HubSpotAPIError)),
    )
    async def search_companies(
        self, query: Optional[str] = None, limit: int = 10
    ) -> dict[str, Any]:
        """Search companies."""
        if query:
            # Use search endpoint for query
            return await self._make_request(
                "POST",
                "/crm/v3/objects/companies/search",
                json_data={
                    "query": query,
                    "limit": limit,
                },
            )
        else:
            # Use list endpoint for all companies
            return await self._make_request(
                "GET",
                "/crm/v3/objects/companies",
                params={"limit": limit},
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (HubSpotRateLimitError, HubSpotAPIError)),
    )
    async def update_contact(
        self, contact_id: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a contact."""
        return await self._make_request(
            "PATCH",
            f"/crm/v3/objects/contacts/{contact_id}",
            json_data={"properties": properties},
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (HubSpotRateLimitError, HubSpotAPIError)),
    )
    async def update_company(
        self, company_id: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a company."""
        return await self._make_request(
            "PATCH",
            f"/crm/v3/objects/companies/{company_id}",
            json_data={"properties": properties},
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (HubSpotRateLimitError, HubSpotAPIError)),
    )
    async def create_note(
        self, contact_id: Optional[str] = None, company_id: Optional[str] = None, note: str = ""
    ) -> dict[str, Any]:
        """Create a note associated with a contact or company."""
        associations = []
        if contact_id:
            associations.append(
                {
                    "to": {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 214}],
                }
            )
        if company_id:
            associations.append(
                {
                    "to": {"id": company_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 279}],
                }
            )

        return await self._make_request(
            "POST",
            "/crm/v3/objects/notes",
            json_data={
                "properties": {
                    "hs_note_body": note,
                },
                "associations": associations,
            },
        )

    async def refresh_access_token(self) -> dict[str, Any]:
        """Refresh the access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        token = await self.oauth.refresh_token(self.refresh_token)
        self.access_token = token["access_token"]
        if "refresh_token" in token:
            self.refresh_token = token["refresh_token"]

        # Call callback if provided to update database
        if self._on_token_refresh:
            expires_in = token.get("expires_in")
            await self._on_token_refresh(
                self.access_token,
                self.refresh_token,
                expires_in,
            )

        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": token.get("expires_at"),
        }

    async def test_connection(self) -> bool:
        """Test if the integration is working."""
        try:
            # Try to get contacts (lightweight request with limit 1)
            await self._make_request(
                "GET",
                "/crm/v3/objects/contacts",
                params={"limit": 1},
            )
            return True
        except Exception:
            return False
