"""Base integration class for all external service integrations."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime


class BaseIntegration(ABC):
    """Base class for all integrations."""

    def __init__(self, access_token: str, refresh_token: Optional[str] = None):
        """Initialize integration with tokens."""
        self.access_token = access_token
        self.refresh_token = refresh_token

    @abstractmethod
    async def refresh_access_token(self) -> dict[str, Any]:
        """Refresh the access token using refresh token."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the integration is working."""
        pass
