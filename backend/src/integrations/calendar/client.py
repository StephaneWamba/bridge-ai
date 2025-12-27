"""Google Calendar API client with quota management and error handling."""

from typing import Any, Optional, List
from datetime import datetime, timedelta, timezone
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


class CalendarQuotaExceededError(Exception):
    """Raised when Calendar API quota is exceeded."""

    pass


class CalendarAPIError(Exception):
    """Raised when Calendar API returns an error."""

    pass


class CalendarClient(BaseIntegration):
    """Google Calendar API client with quota management and retries."""

    # Calendar API quotas (per user per day)
    # Free tier: 1,000,000 quota units per day
    # Each API call consumes quota units (e.g., list: 100, get: 50, insert: 50, update: 100, delete: 50)
    DAILY_QUOTA_UNITS = 1_000_000
    QUOTA_WARNING_THRESHOLD = 0.8  # Warn at 80% usage

    def __init__(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        on_token_refresh: Optional[Any] = None,
    ):
        """Initialize Calendar client.

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
        """Get or create Calendar service instance."""
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
            self._service = build("calendar", "v3", credentials=credentials)
        return self._service

    async def _check_quota(self) -> None:
        """Check if quota is available."""
        if self._quota_used >= self.DAILY_QUOTA_UNITS * self.QUOTA_WARNING_THRESHOLD:
            raise CalendarQuotaExceededError(
                f"Calendar API quota warning: {self._quota_used}/{self.DAILY_QUOTA_UNITS} units used"
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

        # Call refresh callback if provided
        if self._on_token_refresh:
            expires_in = None
            if token.get("expires_at"):
                expires_at = datetime.fromisoformat(
                    token["expires_at"].replace("Z", "+00:00")
                )
                expires_in = int(
                    (expires_at - datetime.utcnow()).total_seconds())
            await self._on_token_refresh(
                token["access_token"],
                token.get("refresh_token", self.refresh_token),
                expires_in,
            )

        return token

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (CalendarQuotaExceededError, CalendarAPIError)),
    )
    async def list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 10,
    ) -> List[dict[str, Any]]:
        """List calendar events.

        Args:
            calendar_id: Calendar ID (default: "primary")
            time_min: Lower bound (exclusive) for an event's end time
            time_max: Upper bound (exclusive) for an event's start time
            max_results: Maximum number of events to return (default: 10)

        Returns:
            List of event dictionaries
        """
        await self._check_quota()

        try:
            service = self._get_service()

            # Build query parameters
            params = {
                "calendarId": calendar_id,
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime",
            }

            # Format datetime for RFC3339 (required by Google Calendar API)
            def format_datetime(dt: datetime) -> str:
                """Format datetime to RFC3339 format for Google Calendar API."""
                # Ensure timezone-aware UTC datetime
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                # Format as RFC3339 (YYYY-MM-DDTHH:MM:SSZ)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

            if time_min:
                params["timeMin"] = format_datetime(time_min)
            if time_max:
                params["timeMax"] = format_datetime(time_max)

            # Execute in thread pool since googleapiclient is synchronous
            def list_events_sync():
                return (
                    service.events()
                    .list(**params)
                    .execute()
                )

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, list_events_sync)

            events = result.get("items", [])
            self._quota_used += 100  # list operation costs 100 quota units

            logger.debug(f"Listed {len(events)} calendar events")
            return events
        except HttpError as e:
            if e.resp.status == 401:
                # Token expired, try refreshing
                await self.refresh_access_token()
                # Retry once after refresh
                service = self._get_service()
                # Format datetime for RFC3339 (required by Google Calendar API)

                def format_datetime(dt: datetime) -> str:
                    """Format datetime to RFC3339 format for Google Calendar API."""
                    # Ensure timezone-aware UTC datetime
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    else:
                        dt = dt.astimezone(timezone.utc)
                    # Format as RFC3339 (YYYY-MM-DDTHH:MM:SSZ)
                    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

                params = {
                    "calendarId": calendar_id,
                    "maxResults": max_results,
                    "singleEvents": True,
                    "orderBy": "startTime",
                }
                if time_min:
                    params["timeMin"] = format_datetime(time_min)
                if time_max:
                    params["timeMax"] = format_datetime(time_max)

                def list_events_sync():
                    return (
                        service.events()
                        .list(**params)
                        .execute()
                    )

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    result = await loop.run_in_executor(executor, list_events_sync)

                events = result.get("items", [])
                self._quota_used += 100
                return events
            elif e.resp.status == 429:
                raise CalendarQuotaExceededError(
                    "Calendar API quota exceeded") from e
            raise CalendarAPIError(f"Calendar API error: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (CalendarQuotaExceededError, CalendarAPIError)),
    )
    async def get_event(
        self, event_id: str, calendar_id: str = "primary"
    ) -> dict[str, Any]:
        """Get a calendar event by ID.

        Args:
            event_id: Event ID
            calendar_id: Calendar ID (default: "primary")

        Returns:
            Event dictionary
        """
        await self._check_quota()

        try:
            service = self._get_service()

            # Execute in thread pool since googleapiclient is synchronous
            def get_event_sync():
                return (
                    service.events()
                    .get(calendarId=calendar_id, eventId=event_id)
                    .execute()
                )

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, get_event_sync)

            self._quota_used += 50  # get operation costs 50 quota units
            return result
        except HttpError as e:
            if e.resp.status == 401:
                await self.refresh_access_token()
                # Retry once after refresh
                service = self._get_service()

                def get_event_sync():
                    return (
                        service.events()
                        .get(calendarId=calendar_id, eventId=event_id)
                        .execute()
                    )

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    result = await loop.run_in_executor(executor, get_event_sync)

                self._quota_used += 50
                return result
            elif e.resp.status == 429:
                raise CalendarQuotaExceededError(
                    "Calendar API quota exceeded") from e
            raise CalendarAPIError(f"Calendar API error: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (CalendarQuotaExceededError, CalendarAPIError)),
    )
    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Create a calendar event.

        Args:
            summary: Event title/summary
            start_time: Event start time
            end_time: Event end time
            description: Event description (optional)
            location: Event location (optional)
            attendees: List of attendee email addresses (optional)
            calendar_id: Calendar ID (default: "primary")

        Returns:
            Created event dictionary
        """
        await self._check_quota()

        try:
            service = self._get_service()

            # Build event body
            event = {
                "summary": summary,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC",
                },
            }

            if description:
                event["description"] = description
            if location:
                event["location"] = location
            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]

            # Execute in thread pool since googleapiclient is synchronous
            def create_event_sync():
                # Build request parameters
                request_params = {
                    "calendarId": calendar_id,
                    "body": event,
                }
                # Send email invitations if attendees are present
                if attendees:
                    request_params["sendUpdates"] = "all"
                return service.events().insert(**request_params).execute()

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, create_event_sync)

            self._quota_used += 50  # insert operation costs 50 quota units
            logger.info(f"Created calendar event: {summary}")

            return result
        except HttpError as e:
            if e.resp.status == 401:
                await self.refresh_access_token()
                # Retry once after refresh
                service = self._get_service()

                def create_event_sync():
                    # Build request parameters
                    request_params = {
                        "calendarId": calendar_id,
                        "body": event,
                    }
                    # Send email invitations if attendees are present
                    if attendees:
                        request_params["sendUpdates"] = "all"
                    return service.events().insert(**request_params).execute()

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    result = await loop.run_in_executor(executor, create_event_sync)

                self._quota_used += 50
                return result
            elif e.resp.status == 429:
                raise CalendarQuotaExceededError(
                    "Calendar API quota exceeded") from e
            raise CalendarAPIError(f"Calendar API error: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (CalendarQuotaExceededError, CalendarAPIError)),
    )
    async def update_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> dict[str, Any]:
        """Update a calendar event.

        Args:
            event_id: Event ID to update
            calendar_id: Calendar ID (default: "primary")
            summary: Event title/summary (optional)
            start_time: Event start time (optional)
            end_time: Event end time (optional)
            description: Event description (optional)
            location: Event location (optional)
            attendees: List of attendee email addresses (optional)

        Returns:
            Updated event dictionary
        """
        await self._check_quota()

        try:
            service = self._get_service()

            # First get the existing event
            def get_event_sync():
                return (
                    service.events()
                    .get(calendarId=calendar_id, eventId=event_id)
                    .execute()
                )

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                existing_event = await loop.run_in_executor(executor, get_event_sync)

            # Update only provided fields
            if summary is not None:
                existing_event["summary"] = summary
            if description is not None:
                existing_event["description"] = description
            if location is not None:
                existing_event["location"] = location

            if start_time is not None:
                if start_time.tzinfo:
                    existing_event["start"] = {
                        "dateTime": start_time.isoformat(), "timeZone": "UTC"}
                else:
                    existing_event["start"] = {
                        "date": start_time.date().isoformat()}

            if end_time is not None:
                if end_time.tzinfo:
                    existing_event["end"] = {
                        "dateTime": end_time.isoformat(), "timeZone": "UTC"}
                else:
                    existing_event["end"] = {
                        "date": end_time.date().isoformat()}

            if attendees is not None:
                existing_event["attendees"] = [
                    {"email": email} for email in attendees
                ]

            # Update the event
            def update_event_sync():
                request_params = {
                    "calendarId": calendar_id,
                    "eventId": event_id,
                    "body": existing_event,
                }
                # Send updates if attendees are present
                if attendees:
                    request_params["sendUpdates"] = "all"
                return service.events().update(**request_params).execute()

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, update_event_sync)

            self._quota_used += 100  # update operation costs 100 quota units
            return result

        except HttpError as e:
            if e.resp.status == 401:
                await self.refresh_access_token()
                # Retry once after refresh
                service = self._get_service()

                def get_event_sync_retry():
                    return (
                        service.events()
                        .get(calendarId=calendar_id, eventId=event_id)
                        .execute()
                    )

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    existing_event = await loop.run_in_executor(
                        executor, get_event_sync_retry
                    )

                if summary is not None:
                    existing_event["summary"] = summary
                if description is not None:
                    existing_event["description"] = description
                if location is not None:
                    existing_event["location"] = location

                if start_time is not None:
                    if start_time.tzinfo:
                        existing_event["start"] = {
                            "dateTime": start_time.isoformat(), "timeZone": "UTC"}
                    else:
                        existing_event["start"] = {
                            "date": start_time.date().isoformat()}

                if end_time is not None:
                    if end_time.tzinfo:
                        existing_event["end"] = {
                            "dateTime": end_time.isoformat(), "timeZone": "UTC"}
                    else:
                        existing_event["end"] = {
                            "date": end_time.date().isoformat()}

                if attendees is not None:
                    existing_event["attendees"] = [
                        {"email": email} for email in attendees
                    ]

                def update_event_sync_retry():
                    request_params = {
                        "calendarId": calendar_id,
                        "eventId": event_id,
                        "body": existing_event,
                    }
                    if attendees:
                        request_params["sendUpdates"] = "all"
                    return service.events().update(**request_params).execute()

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    result = await loop.run_in_executor(
                        executor, update_event_sync_retry
                    )
                self._quota_used += 100
                return result
            elif e.resp.status == 429:
                raise CalendarQuotaExceededError(
                    "Calendar API quota exceeded") from e
            elif e.resp.status == 404:
                raise CalendarAPIError(f"Event {event_id} not found") from e
            error_msg = f"Calendar API error (status {e.resp.status})"
            error_reason = getattr(e, "reason", "")
            if error_reason:
                error_msg += f": {error_reason}"
            logger.error(
                f"Calendar update_event error: {error_msg}", exc_info=True)
            raise CalendarAPIError(error_msg) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (CalendarQuotaExceededError, CalendarAPIError)),
    )
    async def delete_event(
        self, event_id: str, calendar_id: str = "primary"
    ) -> None:
        """Delete a calendar event.

        Args:
            event_id: Event ID to delete
            calendar_id: Calendar ID (default: "primary")
        """
        await self._check_quota()

        try:
            service = self._get_service()

            def delete_event_sync():
                (
                    service.events()
                    .delete(calendarId=calendar_id, eventId=event_id)
                    .execute()
                )

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, delete_event_sync)

            self._quota_used += 50  # delete operation costs 50 quota units

        except HttpError as e:
            if e.resp.status == 401:
                await self.refresh_access_token()
                # Retry once after refresh
                service = self._get_service()

                def delete_event_sync_retry():
                    (
                        service.events()
                        .delete(calendarId=calendar_id, eventId=event_id)
                        .execute()
                    )

                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    await loop.run_in_executor(executor, delete_event_sync_retry)
                self._quota_used += 50
                return
            elif e.resp.status == 429:
                raise CalendarQuotaExceededError(
                    "Calendar API quota exceeded") from e
            elif e.resp.status == 404:
                raise CalendarAPIError(f"Event {event_id} not found") from e
            error_msg = f"Calendar API error (status {e.resp.status})"
            error_reason = getattr(e, "reason", "")
            if error_reason:
                error_msg += f": {error_reason}"
            logger.error(
                f"Calendar delete_event error: {error_msg}", exc_info=True)
            raise CalendarAPIError(error_msg) from e

    async def test_connection(self) -> bool:
        """Test if the Calendar integration is working."""
        try:
            await self.list_events(max_results=1)
            return True
        except Exception:
            return False
