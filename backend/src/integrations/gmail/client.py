"""Gmail API client with quota management and error handling."""

from typing import Any, Optional
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.integrations.base import BaseIntegration
from src.core.logging import logger


class GmailQuotaExceededError(Exception):
    """Raised when Gmail API quota is exceeded."""

    pass


class GmailAPIError(Exception):
    """Raised when Gmail API returns an error."""

    pass


class GmailClient(BaseIntegration):
    """Gmail API client with quota management and retries."""

    # Gmail API quotas (per user per day)
    # Free tier: 1 billion quota units per day
    # Each API call consumes quota units (e.g., list: 5, get: 5, send: 100)
    DAILY_QUOTA_UNITS = 1_000_000_000  # Conservative limit
    QUOTA_WARNING_THRESHOLD = 0.8  # Warn at 80% usage

    def __init__(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        on_token_refresh: Optional[Any] = None,
    ):
        """Initialize Gmail client.

        Args:
            access_token: Google access token
            refresh_token: Google refresh token (optional)
            on_token_refresh: Optional callback when token is refreshed.
                Should accept (access_token, refresh_token, expires_in) as arguments.
        """
        super().__init__(access_token, refresh_token)
        self._on_token_refresh = on_token_refresh
        self._service = None
        self._quota_used = 0
        self._quota_reset_at = datetime.utcnow() + timedelta(days=1)

    def _get_service(self):
        """Get or create Gmail service instance."""
        if self._service is None:
            # Import here to avoid circular dependency
            from src.integrations.gmail.oauth import GoogleOAuth

            oauth = GoogleOAuth()
            credentials = Credentials(
                token=self.access_token,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=oauth.client_id,  # Required for token refresh
                client_secret=oauth.client_secret,  # Required for token refresh
            )
            self._service = build("gmail", "v1", credentials=credentials)
        return self._service

    async def _check_quota(self) -> None:
        """Check if quota is available."""
        if self._quota_used >= self.DAILY_QUOTA_UNITS * self.QUOTA_WARNING_THRESHOLD:
            raise GmailQuotaExceededError(
                f"Gmail API quota warning: {self._quota_used}/{self.DAILY_QUOTA_UNITS} units used"
            )

    async def refresh_access_token(self) -> dict[str, Any]:
        """Refresh the access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        from src.integrations.gmail.oauth import GoogleOAuth

        oauth = GoogleOAuth()
        token = await oauth.refresh_token(self.refresh_token)
        self.access_token = token["access_token"]
        if "refresh_token" in token:
            self.refresh_token = token["refresh_token"]

        # Invalidate service to rebuild with new credentials
        self._service = None

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
            "expires_in": token.get("expires_in"),
        }

    async def _refresh_token_if_needed(self) -> None:
        """Refresh token if expired."""
        # Check if token is expired and refresh if needed
        # This is called before API operations
        try:
            # Try to use the service - if it fails with 401, refresh token
            if self._service is None:
                # Service not created yet, will be created with current token
                return

            # For now, we'll refresh on 401 errors in the API calls
            # A more sophisticated approach would check expiry time
            pass
        except Exception:
            # If there's an error, try refreshing
            if self.refresh_token:
                await self.refresh_access_token()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (GmailQuotaExceededError, GmailAPIError)),
    )
    async def list_messages(
        self,
        query: Optional[str] = None,
        limit: int = 10,
        max_results: Optional[int] = None,
        page_token: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List Gmail messages.

        Args:
            query: Gmail search query (optional)
            limit: Maximum number of messages to return (default: 10)
            max_results: Alias for limit (for backward compatibility)
            page_token: Page token for pagination (optional)

        Returns:
            List of message dictionaries with 'id' and 'threadId' keys
        """
        await self._check_quota()

        # Use limit if provided, otherwise max_results
        max_results = max_results or limit

        try:
            service = self._get_service()

            # Execute in thread pool since googleapiclient is synchronous
            def list_messages_sync():
                return (
                    service.users()
                    .messages()
                    .list(
                        userId="me",
                        q=query,
                        maxResults=max_results,
                        pageToken=page_token,
                    )
                    .execute()
                )

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                results = await loop.run_in_executor(executor, list_messages_sync)

            self._quota_used += 5  # list operation costs 5 quota units

            # Return list of messages (extract from 'messages' key in response)
            return results.get("messages", [])
        except HttpError as e:
            if e.resp.status == 429:
                raise GmailQuotaExceededError(
                    "Gmail API quota exceeded") from e
            raise GmailAPIError(f"Gmail API error: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (GmailQuotaExceededError, GmailAPIError)),
    )
    async def get_message(self, message_id: str) -> dict[str, Any]:
        """Get a specific Gmail message."""
        await self._check_quota()

        try:
            service = self._get_service()

            # Execute in thread pool since googleapiclient is synchronous
            def get_message_sync():
                return (
                    service.users()
                    .messages()
                    .get(userId="me", id=message_id, format="full")
                    .execute()
                )

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                message = await loop.run_in_executor(executor, get_message_sync)

            self._quota_used += 5  # get operation costs 5 quota units

            return message
        except HttpError as e:
            if e.resp.status == 401:
                # Token expired, try to refresh
                if self.refresh_token:
                    logger.info("Gmail token expired, attempting refresh...")
                    await self.refresh_access_token()
                    # Retry the request with new token
                    service = self._get_service()  # Rebuild service with new credentials
                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor() as executor:
                        message = await loop.run_in_executor(executor, get_message_sync)
                    return message
                else:
                    raise GmailAPIError(
                        "Gmail authentication failed - no refresh token available") from e
            elif e.resp.status == 429:
                raise GmailQuotaExceededError(
                    "Gmail API quota exceeded") from e
            raise GmailAPIError(f"Gmail API error: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (GmailQuotaExceededError, GmailAPIError)),
    )
    async def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        body_type: str = "text/plain",
    ) -> dict[str, Any]:
        """Send a new email via Gmail (not a reply)."""
        await self._check_quota()

        try:
            import base64
            from email.mime.text import MIMEText
            from email.utils import formataddr

            # Ensure body is not empty
            if not body or not body.strip():
                raise ValueError("Email body cannot be empty")

            # Log the email details for debugging
            logger.debug(
                f"Sending email to {to}, subject: {subject}, body length: {len(body)}")

            # Create MIMEText message with proper encoding
            # Use _subtype='plain' explicitly to ensure it's plain text (not multipart)
            message = MIMEText(body, _subtype='plain', _charset='utf-8')

            # Set headers - Gmail will automatically set From to authenticated user
            message["to"] = to
            message["subject"] = subject

            # Encode message properly for Gmail API
            # Gmail API requires base64url encoding of the RFC 2822 formatted message
            # Use as_bytes() to get the properly formatted message bytes
            raw_message_bytes = message.as_bytes()

            # Base64url encode - DO NOT remove padding (=)
            # Removing padding causes Gmail to misinterpret the message structure
            # This can result in empty body and "noname" attachments
            raw_message = base64.urlsafe_b64encode(
                raw_message_bytes).decode('ascii')

            # Keep the padding - it's required for proper decoding
            logger.debug(
                f"Encoded message length: {len(raw_message)}, body preview: {body[:50]}...")

            service = self._get_service()

            # Execute in thread pool since googleapiclient is synchronous
            def send_message_sync():
                return (
                    service.users()
                    .messages()
                    .send(userId="me", body={"raw": raw_message})
                    .execute()
                )

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, send_message_sync)

            self._quota_used += 100  # send operation costs 100 quota units

            return result
        except HttpError as e:
            if e.resp.status == 429:
                raise GmailQuotaExceededError(
                    "Gmail API quota exceeded") from e
            raise GmailAPIError(f"Gmail API error: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (GmailQuotaExceededError, GmailAPIError)),
    )
    async def reply_to_message(
        self,
        message_id: str,
        body: str,
        body_type: str = "text/plain",
        include_attachments: bool = False,
    ) -> dict[str, Any]:
        """Reply to an existing email message. Does NOT include attachments from original unless explicitly requested."""
        await self._check_quota()

        try:
            import base64
            from email.mime.text import MIMEText
            from email.utils import make_msgid

            # Get the original message to extract thread ID and headers
            original_message = await self.get_message(message_id)
            thread_id = original_message.get("threadId")

            # Extract headers from original message
            payload = original_message.get("payload", {})
            headers = payload.get("headers", [])
            if isinstance(headers, dict):
                headers = [{"name": k, "value": v} for k, v in headers.items()]

            # Get original subject, sender, and Message-ID
            original_subject = next(
                (h["value"] for h in headers if h["name"] == "Subject"), ""
            )
            original_from = next(
                (h["value"] for h in headers if h["name"] == "From"), ""
            )
            original_message_id = next(
                (h["value"] for h in headers if h["name"] == "Message-ID"), ""
            )

            # Extract email address from "Name <email@example.com>" format
            import re
            from_match = re.search(r'<([^>]+)>', original_from)
            reply_to = from_match.group(
                1) if from_match else original_from.strip()

            # Clean up the email address (remove any extra whitespace)
            reply_to = reply_to.strip()

            # Warn about no-reply addresses (but still allow the reply)
            no_reply_patterns = [
                r'noreply', r'no-reply', r'do-not-reply', r'donotreply',
                r'notifications-noreply', r'notification', r'no_reply'
            ]
            email_lower = reply_to.lower()
            if any(re.search(pattern, email_lower) for pattern in no_reply_patterns):
                logger.warning(
                    f"Attempting to reply to no-reply address: {reply_to}. "
                    "This email may not be monitored and the reply may bounce."
                )

            # Create reply subject (add Re: if not already present)
            if original_subject.startswith("Re:") or original_subject.startswith("RE:"):
                reply_subject = original_subject
            else:
                reply_subject = f"Re: {original_subject}"

            # Ensure body is not empty
            if not body or not body.strip():
                raise ValueError("Reply body cannot be empty")

            # Create reply message - plain text only, no attachments
            # Use _subtype='plain' explicitly to ensure it's plain text (not multipart)
            message = MIMEText(body, _subtype='plain', _charset='utf-8')
            message["to"] = reply_to
            message["subject"] = reply_subject

            # Set proper reply headers for threading
            if original_message_id:
                message["In-Reply-To"] = original_message_id
                message["References"] = original_message_id

            # Encode message properly for Gmail API
            # Use as_bytes() to get the properly formatted message bytes
            raw_message_bytes = message.as_bytes()

            # Base64url encode - DO NOT remove padding (=)
            # Removing padding causes Gmail to misinterpret the message structure
            raw_message = base64.urlsafe_b64encode(
                raw_message_bytes).decode('ascii')

            service = self._get_service()

            # Execute in thread pool since googleapiclient is synchronous
            def reply_message_sync():
                send_body = {"raw": raw_message}
                if thread_id:
                    send_body["threadId"] = thread_id
                return (
                    service.users()
                    .messages()
                    .send(userId="me", body=send_body)
                    .execute()
                )

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, reply_message_sync)

            self._quota_used += 100  # send operation costs 100 quota units

            return result
        except HttpError as e:
            if e.resp.status == 429:
                raise GmailQuotaExceededError(
                    "Gmail API quota exceeded") from e
            raise GmailAPIError(f"Gmail API error: {e}") from e

    async def test_connection(self) -> bool:
        """Test if the Gmail integration is working."""
        try:
            await self.list_messages(max_results=1)
            return True
        except Exception:
            return False
