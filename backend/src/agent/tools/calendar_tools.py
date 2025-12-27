"""Calendar tools for LangChain agent."""

from typing import Optional, Type
from datetime import datetime, timedelta
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.integrations.calendar.client import CalendarClient, CalendarAPIError
from src.services.integration_service import IntegrationService
from src.agent.tools.base import handle_tool_error
from src.core.logging import logger


class ListCalendarEventsInput(BaseModel):
    """Input for listing calendar events."""

    time_min: Optional[str] = Field(
        default=None,
        description="Start time for events (ISO format, e.g., '2025-01-01T00:00:00Z'). If not provided, uses current time."
    )
    time_max: Optional[str] = Field(
        default=None,
        description="End time for events (ISO format, e.g., '2025-01-31T23:59:59Z'). If not provided, uses 30 days from now."
    )
    max_results: int = Field(
        default=10, description="Maximum number of events to return (1-250)"
    )


class ListCalendarEventsTool(BaseTool):
    """Tool for listing calendar events."""

    name: str = "list_calendar_events"
    description: str = (
        "List calendar events from Google Calendar. "
        "Returns a list of events with summary, start time, end time, and description. "
        "Use time_min and time_max to filter events by date range."
    )
    args_schema: Type[BaseModel] = ListCalendarEventsInput
    model_config = {"extra": "allow"}

    def __init__(self, client: CalendarClient, **kwargs):
        """Initialize the tool with a Calendar client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "client", client)

    def _run(self, time_min: Optional[str] = None, time_max: Optional[str] = None, max_results: int = 10) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError("This tool is async-only. Use _arun instead.")

    async def _arun(
        self, time_min: Optional[str] = None, time_max: Optional[str] = None, max_results: int = 10
    ) -> str:
        """List events from Google Calendar."""
        try:
            # Parse time_min and time_max if provided
            from datetime import timezone
            
            time_min_dt = None
            if time_min:
                try:
                    time_min_dt = datetime.fromisoformat(time_min.replace("Z", "+00:00"))
                except ValueError:
                    return "Invalid time_min format. Use ISO format (e.g., '2025-01-01T00:00:00Z')."
            else:
                time_min_dt = datetime.now(timezone.utc)

            time_max_dt = None
            if time_max:
                try:
                    time_max_dt = datetime.fromisoformat(time_max.replace("Z", "+00:00"))
                except ValueError:
                    return "Invalid time_max format. Use ISO format (e.g., '2025-01-31T23:59:59Z')."
            else:
                time_max_dt = datetime.now(timezone.utc) + timedelta(days=30)

            events = await self.client.list_events(
                time_min=time_min_dt,
                time_max=time_max_dt,
                max_results=min(max_results, 250),
            )

            if not events:
                return "No calendar events found in the specified time range."

            formatted = []
            for event in events:
                summary = event.get("summary", "No title")
                start = event.get("start", {})
                end = event.get("end", {})
                description = event.get("description", "")
                location = event.get("location", "")
                event_id = event.get("id", "unknown")

                # Parse start/end times
                start_time = start.get("dateTime") or start.get("date", "")
                end_time = end.get("dateTime") or end.get("date", "")

                event_str = f"- Summary: {summary}\n  Event ID: {event_id}\n  Start: {start_time}\n  End: {end_time}"
                if location:
                    event_str += f"\n  Location: {location}"
                if description:
                    event_str += f"\n  Description: {description[:100]}..."
                formatted.append(event_str)

            return f"Found {len(events)} event(s):\n\n" + "\n\n".join(formatted)
        except CalendarAPIError as e:
            return handle_tool_error(e, "Calendar")
        except Exception as e:
            logger.error(f"Unexpected error listing calendar events: {e}", exc_info=True)
            return f"Error listing calendar events: {str(e)}"


class CreateCalendarEventInput(BaseModel):
    """Input for creating a calendar event."""

    summary: str = Field(description="Event title/summary")
    start_time: str = Field(
        description="Event start time (ISO format, e.g., '2025-01-15T14:00:00Z')"
    )
    end_time: str = Field(
        description="Event end time (ISO format, e.g., '2025-01-15T15:00:00Z')"
    )
    description: Optional[str] = Field(
        default=None, description="Event description (optional)"
    )
    location: Optional[str] = Field(
        default=None, description="Event location (optional)"
    )
    attendees: Optional[list[str]] = Field(
        default=None, description="List of attendee email addresses (optional)"
    )


class CreateCalendarEventTool(BaseTool):
    """Tool for creating calendar events."""

    name: str = "create_calendar_event"
    description: str = (
        "Create a new calendar event in Google Calendar. "
        "Requires summary, start_time, and end_time. "
        "Optionally include description, location, and attendees."
    )
    args_schema: Type[BaseModel] = CreateCalendarEventInput
    model_config = {"extra": "allow"}

    def __init__(self, client: CalendarClient, **kwargs):
        """Initialize the tool with a Calendar client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "client", client)

    def _run(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
    ) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError("This tool is async-only. Use _arun instead.")

    async def _arun(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
    ) -> str:
        """Create a calendar event."""
        try:
            # Parse start_time and end_time
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            except ValueError:
                return "Invalid start_time format. Use ISO format (e.g., '2025-01-15T14:00:00Z')."

            try:
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            except ValueError:
                return "Invalid end_time format. Use ISO format (e.g., '2025-01-15T15:00:00Z')."

            if end_dt <= start_dt:
                return "Error: end_time must be after start_time."

            result = await self.client.create_event(
                summary=summary,
                start_time=start_dt,
                end_time=end_dt,
                description=description,
                location=location,
                attendees=attendees,
            )

            event_id = result.get("id", "unknown")
            html_link = result.get("htmlLink", "")

            response = f"Calendar event created successfully! Event ID: {event_id}."
            if html_link:
                response += f" View event: {html_link}"

            return response
        except CalendarAPIError as e:
            return handle_tool_error(e, "Calendar")
        except Exception as e:
            logger.error(f"Unexpected error creating calendar event: {e}", exc_info=True)
            return f"Error creating calendar event: {str(e)}"


class GetCalendarEventInput(BaseModel):
    """Input for getting a calendar event."""

    event_id: str = Field(description="Event ID to retrieve")
    calendar_id: str = Field(
        default="primary", description='Calendar ID (default: "primary")'
    )


class GetCalendarEventTool(BaseTool):
    """Tool for getting a calendar event by ID."""

    name: str = "get_calendar_event"
    description: str = (
        "Get detailed information about a specific calendar event by its ID. "
        "Returns full event details including summary, description, location, attendees, and times."
    )
    args_schema: Type[BaseModel] = GetCalendarEventInput
    model_config = {"extra": "allow"}

    def __init__(self, client: CalendarClient, **kwargs):
        """Initialize the tool with a Calendar client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "client", client)

    def _run(self, event_id: str, calendar_id: str = "primary") -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError("This tool is async-only. Use _arun instead.")

    async def _arun(self, event_id: str, calendar_id: str = "primary") -> str:
        """Get a calendar event by ID."""
        try:
            event = await self.client.get_event(event_id, calendar_id)

            summary = event.get("summary", "No title")
            start = event.get("start", {})
            end = event.get("end", {})
            description = event.get("description", "")
            location = event.get("location", "")
            attendees = event.get("attendees", [])
            html_link = event.get("htmlLink", "")

            start_time = start.get("dateTime") or start.get("date", "")
            end_time = end.get("dateTime") or end.get("date", "")

            result = f"Event Details:\n"
            result += f"- Summary: {summary}\n"
            result += f"- Event ID: {event_id}\n"
            result += f"- Start: {start_time}\n"
            result += f"- End: {end_time}\n"

            if location:
                result += f"- Location: {location}\n"
            if description:
                result += f"- Description: {description}\n"
            if attendees:
                attendee_emails = [a.get("email", "") for a in attendees if a.get("email")]
                if attendee_emails:
                    result += f"- Attendees: {', '.join(attendee_emails)}\n"
            if html_link:
                result += f"- Link: {html_link}\n"

            return result
        except CalendarAPIError as e:
            return handle_tool_error(e, "Calendar")
        except Exception as e:
            logger.error(f"Unexpected error getting calendar event: {e}", exc_info=True)
            return f"Error getting calendar event: {str(e)}"


class UpdateCalendarEventInput(BaseModel):
    """Input for updating a calendar event."""

    event_id: str = Field(description="Event ID to update")
    calendar_id: str = Field(
        default="primary", description='Calendar ID (default: "primary")'
    )
    summary: Optional[str] = Field(default=None, description="Event title/summary (optional)")
    start_time: Optional[str] = Field(
        default=None, description="Event start time in ISO format (optional)"
    )
    end_time: Optional[str] = Field(
        default=None, description="Event end time in ISO format (optional)"
    )
    description: Optional[str] = Field(
        default=None, description="Event description (optional)"
    )
    location: Optional[str] = Field(default=None, description="Event location (optional)")
    attendees: Optional[list[str]] = Field(
        default=None, description="List of attendee email addresses (optional)"
    )


class UpdateCalendarEventTool(BaseTool):
    """Tool for updating a calendar event."""

    name: str = "update_calendar_event"
    description: str = (
        "Update an existing calendar event. Provide the event_id and the fields you want to update "
        "(summary, start_time, end_time, description, location, attendees). Only provided fields will be updated."
    )
    args_schema: Type[BaseModel] = UpdateCalendarEventInput
    model_config = {"extra": "allow"}

    def __init__(self, client: CalendarClient, **kwargs):
        """Initialize the tool with a Calendar client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "client", client)

    def _run(
        self,
        event_id: str,
        calendar_id: str = "primary",
        summary: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
    ) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError("This tool is async-only. Use _arun instead.")

    async def _arun(
        self,
        event_id: str,
        calendar_id: str = "primary",
        summary: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
    ) -> str:
        """Update a calendar event."""
        try:
            from datetime import timezone

            start_dt = None
            if start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                except ValueError:
                    return "Invalid start_time format. Use ISO format (e.g., '2025-01-15T14:00:00Z')."

            end_dt = None
            if end_time:
                try:
                    end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                except ValueError:
                    return "Invalid end_time format. Use ISO format (e.g., '2025-01-15T15:00:00Z')."

            if start_dt and end_dt and end_dt <= start_dt:
                return "Error: end_time must be after start_time."

            result = await self.client.update_event(
                event_id=event_id,
                calendar_id=calendar_id,
                summary=summary,
                start_time=start_dt,
                end_time=end_dt,
                description=description,
                location=location,
                attendees=attendees,
            )

            event_id_result = result.get("id", event_id)
            html_link = result.get("htmlLink", "")

            response = f"Calendar event updated successfully! Event ID: {event_id_result}."
            if html_link:
                response += f" View event: {html_link}"

            return response
        except CalendarAPIError as e:
            return handle_tool_error(e, "Calendar")
        except Exception as e:
            logger.error(f"Unexpected error updating calendar event: {e}", exc_info=True)
            return f"Error updating calendar event: {str(e)}"


class DeleteCalendarEventInput(BaseModel):
    """Input for deleting a calendar event."""

    event_id: str = Field(description="Event ID to delete")
    calendar_id: str = Field(
        default="primary", description='Calendar ID (default: "primary")'
    )


class DeleteCalendarEventTool(BaseTool):
    """Tool for deleting a calendar event."""

    name: str = "delete_calendar_event"
    description: str = (
        "Delete a calendar event by its ID. This action cannot be undone. "
        "Use with caution - the event will be permanently removed from the calendar."
    )
    args_schema: Type[BaseModel] = DeleteCalendarEventInput
    model_config = {"extra": "allow"}

    def __init__(self, client: CalendarClient, **kwargs):
        """Initialize the tool with a Calendar client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "client", client)

    def _run(self, event_id: str, calendar_id: str = "primary") -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError("This tool is async-only. Use _arun instead.")

    async def _arun(self, event_id: str, calendar_id: str = "primary") -> str:
        """Delete a calendar event."""
        try:
            await self.client.delete_event(event_id, calendar_id)
            return f"Calendar event {event_id} deleted successfully."
        except CalendarAPIError as e:
            return handle_tool_error(e, "Calendar")
        except Exception as e:
            logger.error(f"Unexpected error deleting calendar event: {e}", exc_info=True)
            return f"Error deleting calendar event: {str(e)}"


async def get_calendar_tools(db, user_id: str) -> list[BaseTool]:
    """Get all Calendar tools for a user."""
    client = await IntegrationService.get_calendar_client(db, user_id)

    if not client:
        return []  # No Calendar integration connected

    return [
        ListCalendarEventsTool(client),
        CreateCalendarEventTool(client),
        GetCalendarEventTool(client),
        UpdateCalendarEventTool(client),
        DeleteCalendarEventTool(client),
    ]

