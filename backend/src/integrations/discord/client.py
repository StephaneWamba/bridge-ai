"""Discord API client with rate limiting and error handling."""

import asyncio
from typing import Any, Optional
from datetime import datetime, timedelta
from httpx import AsyncClient, HTTPStatusError, Response
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.integrations.base import BaseIntegration
from src.core.logging import logger


class DiscordRateLimitError(Exception):
    """Raised when Discord rate limit is exceeded."""

    pass


class DiscordAPIError(Exception):
    """Raised when Discord API returns an error."""

    pass


class DiscordClient(BaseIntegration):
    """Discord API client with rate limiting and retries.

    Discord bots use static Bot tokens (not OAuth refresh tokens).
    The token is provided in the constructor and does not change.
    """

    BASE_URL = "https://discord.com/api/v10"
    # Discord rate limit: 5 requests per second per bot (globally)
    RATE_LIMIT_REQUESTS = 5
    RATE_LIMIT_WINDOW = 1  # seconds

    def __init__(self, bot_token: str):
        """Initialize Discord client.

        Args:
            bot_token: Discord bot token (static, no refresh token needed)
        """
        # For Discord, access_token is the bot_token (no refresh token)
        super().__init__(access_token=bot_token, refresh_token=None)
        self.bot_token = bot_token
        self._rate_limit_queue: list[datetime] = []
        self._lock = asyncio.Lock()

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
        """Make HTTP request to Discord API with rate limiting and retries."""
        await self._wait_for_rate_limit()

        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (BridgeAI, 1.0)",
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
                # Discord API returns empty body for some endpoints (e.g., 204 No Content)
                if response.status_code == 204:
                    return {}
                return response.json()
            except HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Discord rate limit response includes retry_after
                    retry_after = e.response.headers.get("Retry-After", "1")
                    raise DiscordRateLimitError(
                        f"Discord rate limit exceeded. Retry after {retry_after} seconds"
                    ) from e
                elif e.response.status_code == 401:
                    raise DiscordAPIError(
                        "Discord authentication failed - invalid bot token"
                    ) from e
                elif e.response.status_code == 403:
                    raise DiscordAPIError(
                        "Discord permission denied - bot lacks required permissions"
                    ) from e
                elif e.response.status_code == 404:
                    raise DiscordAPIError(
                        "Discord resource not found - invalid channel or guild ID"
                    ) from e
                error_message = "Unknown error"
                try:
                    error_json = e.response.json()
                    error_message = error_json.get("message", str(e))
                except Exception:
                    error_message = str(e)
                raise DiscordAPIError(
                    f"Discord API error: {error_message}") from e
            except Exception as e:
                raise DiscordAPIError(
                    f"Discord request failed: {str(e)}") from e

    async def refresh_access_token(self) -> dict[str, Any]:
        """Discord bots use static tokens, so refresh is not applicable.

        This method exists to satisfy the BaseIntegration interface but will raise an error.
        """
        raise NotImplementedError(
            "Discord bots use static tokens - refresh is not applicable"
        )

    async def test_connection(self) -> bool:
        """Test if the Discord integration is working by fetching bot user info."""
        try:
            await self.get_bot_user()
            return True
        except Exception:
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(
            (DiscordRateLimitError, DiscordAPIError)),
    )
    async def get_bot_user(self) -> dict[str, Any]:
        """Get the bot user information.

        Returns:
            Bot user object with id, username, discriminator, etc.
        """
        return await self._make_request("GET", "/users/@me")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(
            (DiscordRateLimitError, DiscordAPIError)),
    )
    async def send_message(
        self, channel_id: str, content: str
    ) -> dict[str, Any]:
        """Send a message to a Discord channel.

        Args:
            channel_id: Discord channel ID (snowflake string)
            content: Message content (text)

        Returns:
            Message object with id, channel_id, content, etc.
        """
        json_data = {"content": content}
        return await self._make_request(
            "POST", f"/channels/{channel_id}/messages", json_data=json_data
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(
            (DiscordRateLimitError, DiscordAPIError)),
    )
    async def get_messages(
        self, channel_id: str, limit: int = 50, before: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Get messages from a Discord channel.

        Args:
            channel_id: Discord channel ID (snowflake string)
            limit: Maximum number of messages to return (1-100, default: 50)
            before: Get messages before this message ID (optional, for pagination)

        Returns:
            List of message objects
        """
        # Clamp limit to Discord's maximum
        limit = max(1, min(100, limit))

        params: dict[str, Any] = {"limit": limit}
        if before:
            params["before"] = before

        return await self._make_request(
            "GET", f"/channels/{channel_id}/messages", params=params
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(
            (DiscordRateLimitError, DiscordAPIError)),
    )
    async def list_channels(self, guild_id: str) -> list[dict[str, Any]]:
        """List channels in a Discord guild (server).

        Args:
            guild_id: Discord guild (server) ID (snowflake string)

        Returns:
            List of channel objects with id, name, type, etc.
        """
        return await self._make_request("GET", f"/guilds/{guild_id}/channels")



