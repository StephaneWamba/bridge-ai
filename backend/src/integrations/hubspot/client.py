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
from src.core.logging import logger


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
        # Cache for association type IDs (to avoid querying every time)
        self._association_type_cache: dict[tuple[str, str], int] = {}

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
                        try:
                            logger.info(
                                "HubSpot token expired, attempting refresh...")
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
                            logger.info(
                                "HubSpot request succeeded after token refresh")
                            return response.json()
                        except Exception as refresh_error:
                            logger.error(
                                f"HubSpot token refresh failed: {refresh_error}", exc_info=True)
                            raise HubSpotAPIError(
                                f"Unauthorized - token expired and refresh failed: {str(refresh_error)}"
                            ) from refresh_error
                    raise HubSpotAPIError(
                        "Unauthorized - token expired and no refresh token available")
                else:
                    error_detail = e.response.text if e.response else "Unknown error"
                    # Log the full error for debugging
                    logger.error(
                        f"HubSpot API error {e.response.status_code}: {error_detail}"
                    )
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
        """Update a contact. Verifies the contact exists before updating."""
        # Verify contact exists first
        try:
            await self.get_contact(contact_id)
        except Exception as e:
            logger.warning(
                f"Contact {contact_id} verification failed: {e}")
            raise HubSpotAPIError(
                f"Contact {contact_id} not found or inaccessible: {e}")
        
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
        from datetime import datetime

        # HubSpot requires hs_timestamp (Unix timestamp in milliseconds)
        # Use current timestamp if not provided
        timestamp_ms = int(datetime.utcnow().timestamp() * 1000)

        # Build the request payload
        payload = {
            "properties": {
                "hs_note_body": note,
                "hs_timestamp": timestamp_ms,  # Required by HubSpot
            }
        }

        # Add associations only if contact_id or company_id is provided
        # Verify the objects exist before creating associations
        associations = []
        if contact_id:
            # Verify contact exists first
            try:
                await self.get_contact(contact_id)
            except Exception as e:
                logger.warning(
                    f"Contact {contact_id} verification failed: {e}")
                raise HubSpotAPIError(
                    f"Contact {contact_id} not found or inaccessible: {e}")

            # Get the correct association type ID from HubSpot API
            # Note: We're creating a note (from) and associating it with a contact (to)
            # So we query: notes -> contacts
            association_type_id = await self.get_association_type_id("notes", "contacts")
            associations.append(
                {
                    "to": {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": association_type_id}],
                }
            )

        if company_id:
            # Verify company exists first
            try:
                await self.get_company(company_id)
            except Exception as e:
                logger.warning(
                    f"Company {company_id} verification failed: {e}")
                raise HubSpotAPIError(
                    f"Company {company_id} not found or inaccessible: {e}")

            # Get the correct association type ID from HubSpot API
            # Note: We're creating a note (from) and associating it with a company (to)
            # So we query: notes -> companies
            association_type_id = await self.get_association_type_id("notes", "companies")
            associations.append(
                {
                    "to": {"id": company_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": association_type_id}],
                }
            )

        if associations:
            payload["associations"] = associations

        return await self._make_request(
            "POST",
            "/crm/v3/objects/notes",
            json_data=payload,
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

    async def get_association_type_id(
        self, from_object_type: str, to_object_type: str
    ) -> int:
        """Get the association type ID for a specific object relationship.
        
        Queries HubSpot API to get the correct association type ID for the account.
        This is the safe way that works for all HubSpot accounts.
        
        Args:
            from_object_type: Source object type (e.g., "contacts", "companies", "notes")
            to_object_type: Target object type (e.g., "contacts", "companies", "notes")
            
        Returns:
            The association type ID for this relationship
            
        Raises:
            HubSpotAPIError: If the association type cannot be found
        """
        # Check cache first
        cache_key = (from_object_type, to_object_type)
        if cache_key in self._association_type_cache:
            return self._association_type_cache[cache_key]
        
        # Try the forward direction first (from -> to)
        endpoint = f"/crm/v4/associations/{from_object_type}/{to_object_type}/labels"
        try:
            response = await self._make_request("GET", endpoint)
            results = response.get("results", [])
            
            if results:
                # Get the first result (usually there's only one)
                association_type_id = results[0].get("typeId") or results[0].get("id")
                
                if association_type_id:
                    # Cache the result
                    self._association_type_cache[cache_key] = association_type_id
                    
                    logger.info(
                        f"Found association type ID {association_type_id} for {from_object_type} -> {to_object_type}"
                    )
                    
                    return association_type_id
        except Exception as e:
            logger.debug(
                f"Forward direction failed for {from_object_type} -> {to_object_type}, trying reverse: {e}"
            )
        
        # Try reverse direction if forward fails (associations might be bidirectional)
        reverse_endpoint = f"/crm/v4/associations/{to_object_type}/{from_object_type}/labels"
        try:
            response = await self._make_request("GET", reverse_endpoint)
            results = response.get("results", [])
            
            if not results:
                raise HubSpotAPIError(
                    f"No association type found for {from_object_type} -> {to_object_type} (tried both directions)"
                )
            
            # Get the first result
            association_type_id = results[0].get("typeId") or results[0].get("id")
            
            if not association_type_id:
                raise HubSpotAPIError(
                    f"Invalid association type response for {from_object_type} -> {to_object_type}"
                )
            
            # Cache the result (for both directions since they're the same)
            self._association_type_cache[cache_key] = association_type_id
            self._association_type_cache[(to_object_type, from_object_type)] = association_type_id
            
            logger.info(
                f"Found association type ID {association_type_id} for {from_object_type} -> {to_object_type} (via reverse lookup)"
            )
            
            return association_type_id
        except Exception as e:
            logger.error(
                f"Error getting association type ID for {from_object_type} -> {to_object_type}: {e}",
                exc_info=True,
            )
            raise HubSpotAPIError(
                f"Failed to get association type ID: {e}"
            ) from e

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
