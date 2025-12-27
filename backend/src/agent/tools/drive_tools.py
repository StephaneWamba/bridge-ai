"""Drive tools for accessing meeting transcripts."""

from typing import Optional, Type
from datetime import datetime, timezone
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.integrations.drive.client import DriveClient, DriveAPIError
from src.integrations.calendar.client import CalendarClient
from src.services.integration_service import IntegrationService
from src.agent.tools.base import handle_tool_error
from src.core.logging import logger


class ReadMeetingTranscriptInput(BaseModel):
    """Input for reading a meeting transcript."""

    event_id: str = Field(description="Google Calendar event ID")
    calendar_id: Optional[str] = Field(
        default="primary", description="Calendar ID (default: 'primary')"
    )


class ReadMeetingTranscriptTool(BaseTool):
    """Tool for reading meeting transcripts from Google Drive."""

    name: str = "read_meeting_transcript"
    description: str = (
        "Read a meeting transcript from Google Drive for a specific calendar event. "
        "Searches for transcript files that match the meeting by date/time. "
        "Returns the transcript text content. Requires event_id from a calendar event."
    )
    args_schema: Type[BaseModel] = ReadMeetingTranscriptInput
    model_config = {"extra": "allow"}

    def __init__(self, drive_client: DriveClient, calendar_client: CalendarClient, **kwargs):
        """Initialize the tool with Drive and Calendar clients."""
        super().__init__(**kwargs)
        object.__setattr__(self, "drive_client", drive_client)
        object.__setattr__(self, "calendar_client", calendar_client)

    def _run(self, event_id: str, calendar_id: str = "primary") -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, event_id: str, calendar_id: str = "primary") -> str:
        """Read meeting transcript from Google Drive."""
        try:
            # First, get the calendar event to extract meeting information
            try:
                event = await self.calendar_client.get_event(event_id, calendar_id)
            except Exception as e:
                return f"Error fetching calendar event: {str(e)}"

            # Extract event information for matching
            summary = event.get("summary", "")
            start = event.get("start", {})
            start_time_str = start.get("dateTime") or start.get("date", "")

            # Parse start time
            try:
                if "T" in start_time_str:
                    start_dt = datetime.fromisoformat(
                        start_time_str.replace("Z", "+00:00"))
                else:
                    start_dt = datetime.fromisoformat(
                        start_time_str).replace(tzinfo=timezone.utc)
            except (ValueError, AttributeError):
                return f"Error parsing event start time: {start_time_str}"

            # Search for transcript files in Drive
            # Google Meet transcripts are typically saved as .txt files or Google Docs
            # Search by date range (transcripts created around the meeting time)
            # Also search for files with "transcript" or meeting-related keywords in name

            # Search queries: transcripts created on or after the meeting start time
            # We'll search for files modified around the meeting time (within 2 hours before/after)
            from datetime import timedelta

            time_window_start = start_dt - timedelta(hours=2)
            time_window_end = start_dt + timedelta(hours=2)

            # Format dates for Drive query (RFC 3339 format)
            time_start_str = time_window_start.strftime("%Y-%m-%dT%H:%M:%SZ")
            time_end_str = time_window_end.strftime("%Y-%m-%dT%H:%M:%SZ")

            # Build search query
            # Search for text files or Google Docs with "transcript" in name, created around meeting time
            query = (
                f"(name contains 'transcript' or name contains 'Transcript' or name contains 'TRANSCRIPT') "
                f"and (mimeType='text/plain' or mimeType='text/html' or mimeType='application/vnd.google-apps.document') "
                f"and modifiedTime >= '{time_start_str}' "
                f"and modifiedTime <= '{time_end_str}' "
                f"and trashed=false"
            )

            # Alternative: search for files with meeting summary in name (if meeting name is descriptive)
            if summary:
                # Escape quotes in summary for query
                summary_escaped = summary.replace("'", "\\'")
                query_alt = (
                    f"(name contains '{summary_escaped}' or name contains 'transcript' or name contains 'Transcript') "
                    f"and (mimeType='text/plain' or mimeType='text/html' or mimeType='application/vnd.google-apps.document') "
                    f"and modifiedTime >= '{time_start_str}' "
                    f"and trashed=false"
                )
            else:
                query_alt = query

            # Try both queries
            files = []
            try:
                files = await self.drive_client.search_files(query, max_results=5)
            except Exception as e:
                logger.warning(f"First transcript search failed: {e}")

            # If no results, try alternative query
            if not files and summary:
                try:
                    files = await self.drive_client.search_files(query_alt, max_results=5)
                except Exception as e:
                    logger.warning(
                        f"Alternative transcript search failed: {e}")

            if not files:
                return (
                    f"No transcript found for meeting '{summary}' (Event ID: {event_id}) "
                    f"on {start_dt.strftime('%Y-%m-%d %H:%M UTC')}. "
                    f"Transcripts may not be available, or they may be saved with a different name/date. "
                    f"Ensure transcripts are saved to Google Drive after the meeting."
                )

            # If multiple files found, use the one closest to the meeting time
            # Sort by modifiedTime closest to meeting start time
            best_match = None
            min_time_diff = float("inf")

            for file in files:
                modified_time_str = file.get("modifiedTime", "")
                if modified_time_str:
                    try:
                        # Parse RFC 3339 format
                        modified_dt = datetime.fromisoformat(
                            modified_time_str.replace("Z", "+00:00"))
                        time_diff = abs(
                            (modified_dt - start_dt).total_seconds())
                        if time_diff < min_time_diff:
                            min_time_diff = time_diff
                            best_match = file
                    except (ValueError, AttributeError):
                        continue

            if not best_match:
                best_match = files[0]  # Fallback to first file

            # Download the transcript file
            file_id = best_match["id"]
            file_name = best_match.get("name", "Unknown")

            try:
                transcript_content = await self.drive_client.download_file(file_id)

                return (
                    f"Transcript for meeting '{summary}' (Event ID: {event_id}):\n"
                    f"File: {file_name}\n"
                    f"Meeting Date: {start_dt.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                    f"{transcript_content}"
                )
            except Exception as e:
                return f"Error downloading transcript file '{file_name}': {str(e)}"

        except DriveAPIError as e:
            return handle_tool_error(e, "Drive")
        except Exception as e:
            logger.error(
                f"Unexpected error reading meeting transcript: {e}", exc_info=True)
            return f"Error reading meeting transcript: {str(e)}"


class ListTranscriptFilesInput(BaseModel):
    """Input for listing transcript files."""

    max_results: int = Field(
        default=20,
        description="Maximum number of transcript files to return (default: 20)",
    )


class ListTranscriptFilesTool(BaseTool):
    """Tool for listing all transcript files in Google Drive."""

    name: str = "list_transcript_files"
    description: str = (
        "List all meeting transcript files in Google Drive. "
        "Searches for files with 'transcript' in the filename across the entire Drive. "
        "Returns a list of transcript files with their names, IDs, modification dates, and links. "
        "Use this to find available transcripts before reading them."
    )
    args_schema: Type[BaseModel] = ListTranscriptFilesInput
    model_config = {"extra": "allow"}

    def __init__(self, drive_client: DriveClient, **kwargs):
        """Initialize the tool with Drive client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "drive_client", drive_client)

    def _run(self, max_results: int = 20) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, max_results: int = 20) -> str:
        """List all transcript files in Google Drive."""
        try:
            # Build search query for transcript files
            # Search for files with "transcript" in name (case-insensitive)
            query = (
                "(name contains 'transcript' or name contains 'Transcript' or name contains 'TRANSCRIPT') "
                "and (mimeType='text/plain' or mimeType='text/html' or mimeType='application/vnd.google-apps.document') "
                "and trashed=false"
            )

            files = await self.drive_client.search_files(
                query=query,
                fields="files(id, name, mimeType, createdTime, modifiedTime, webViewLink)",
                max_results=max_results,
            )

            if not files:
                return "No transcript files found in Google Drive. Make sure transcripts are saved with 'transcript' in the filename."

            # Format results
            formatted = []
            for idx, file in enumerate(files, 1):
                file_name = file.get("name", "Unknown")
                file_id = file.get("id", "unknown")
                modified_time = file.get("modifiedTime", "Unknown")
                mime_type = file.get("mimeType", "")
                web_link = file.get("webViewLink", "")

                # Parse and format date
                try:
                    modified_dt = datetime.fromisoformat(
                        modified_time.replace("Z", "+00:00"))
                    formatted_date = modified_dt.strftime("%Y-%m-%d %H:%M UTC")
                except (ValueError, AttributeError):
                    formatted_date = modified_time

                file_type = "Google Doc" if "google-apps.document" in mime_type else "Text file"

                file_info = f"{idx}. **{file_name}**\n"
                file_info += f"   - File ID: {file_id}\n"
                file_info += f"   - Type: {file_type}\n"
                file_info += f"   - Modified: {formatted_date}"
                if web_link:
                    file_info += f"\n   - Link: {web_link}"

                formatted.append(file_info)

            return f"Found {len(files)} transcript file(s) in Google Drive:\n\n" + "\n\n".join(formatted)

        except DriveAPIError as e:
            return handle_tool_error(e, "Drive")
        except Exception as e:
            logger.error(
                f"Unexpected error listing transcript files: {e}", exc_info=True)
            return f"Error listing transcript files: {str(e)}"


class ReadTranscriptFileInput(BaseModel):
    """Input for reading a transcript file by ID."""

    file_id: str = Field(
        description="Google Drive file ID of the transcript file")


class ReadTranscriptFileTool(BaseTool):
    """Tool for reading a transcript file from Google Drive by file ID."""

    name: str = "read_transcript_file"
    description: str = (
        "Read a transcript file from Google Drive by its file ID. "
        "Use this after listing transcript files with list_transcript_files to get the file_id. "
        "Returns the full transcript content as text."
    )
    args_schema: Type[BaseModel] = ReadTranscriptFileInput
    model_config = {"extra": "allow"}

    def __init__(self, drive_client: DriveClient, **kwargs):
        """Initialize the tool with Drive client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "drive_client", drive_client)

    def _run(self, file_id: str) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, file_id: str) -> str:
        """Read a transcript file from Google Drive by file ID."""
        try:
            # First get file metadata to show file info
            try:
                metadata = await self.drive_client.get_file_metadata(file_id)
                file_name = metadata.get("name", "Unknown")
            except Exception as e:
                return f"Error fetching file metadata: {str(e)}. Please verify the file_id is correct."

            # Download the file content
            try:
                transcript_content = await self.drive_client.download_file(file_id)
                return (
                    f"Transcript file: {file_name}\n"
                    f"File ID: {file_id}\n\n"
                    f"{transcript_content}"
                )
            except Exception as e:
                return f"Error downloading transcript file '{file_name}': {str(e)}"

        except DriveAPIError as e:
            return handle_tool_error(e, "Drive")
        except Exception as e:
            logger.error(
                f"Unexpected error reading transcript file: {e}", exc_info=True)
            return f"Error reading transcript file: {str(e)}"


class CreateDriveFileInput(BaseModel):
    """Input for creating a Drive file."""

    name: str = Field(description="File name")
    content: str = Field(description="File content (text)")
    mime_type: str = Field(
        default="text/plain",
        description="MIME type: 'text/plain' for text files, 'application/vnd.google-apps.document' for Google Docs"
    )
    folder_id: Optional[str] = Field(
        default=None,
        description="Optional parent folder ID"
    )


class CreateDriveFileTool(BaseTool):
    """Tool for creating files in Google Drive."""

    name: str = "create_drive_file"
    description: str = (
        "Create a new file in Google Drive. "
        "Supports text files (text/plain) and Google Docs (application/vnd.google-apps.document). "
        "Returns the created file's ID, name, and link."
    )
    args_schema: Type[BaseModel] = CreateDriveFileInput
    model_config = {"extra": "allow"}

    def __init__(self, drive_client: DriveClient, **kwargs):
        """Initialize the tool with Drive client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "drive_client", drive_client)

    def _run(self, name: str, content: str, mime_type: str = "text/plain", folder_id: Optional[str] = None) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, name: str, content: str, mime_type: str = "text/plain", folder_id: Optional[str] = None) -> str:
        """Create a file in Google Drive."""
        try:
            file_result = await self.drive_client.create_file(
                name=name,
                content=content,
                mime_type=mime_type,
                folder_id=folder_id
            )

            file_id = file_result.get("id", "unknown")
            file_name = file_result.get("name", name)
            web_link = file_result.get("webViewLink", "")

            result = f"File created successfully!\n"
            result += f"- Name: {file_name}\n"
            result += f"- File ID: {file_id}\n"
            if web_link:
                result += f"- Link: {web_link}\n"

            if mime_type == "application/vnd.google-apps.document":
                result += "\nNote: Google Docs were created. Content update requires Google Docs API integration."

            return result

        except DriveAPIError as e:
            return handle_tool_error(e, "Drive")
        except Exception as e:
            logger.error(
                f"Unexpected error creating Drive file: {e}", exc_info=True)
            return f"Error creating file: {str(e)}"


class UpdateDriveFileInput(BaseModel):
    """Input for updating a Drive file."""

    file_id: str = Field(description="Google Drive file ID to update")
    content: str = Field(description="New file content (text)")


class UpdateDriveFileTool(BaseTool):
    """Tool for updating file content in Google Drive."""

    name: str = "update_drive_file"
    description: str = (
        "Update the content of an existing file in Google Drive. "
        "Currently supports text files. Google Docs require Google Docs API integration."
    )
    args_schema: Type[BaseModel] = UpdateDriveFileInput
    model_config = {"extra": "allow"}

    def __init__(self, drive_client: DriveClient, **kwargs):
        """Initialize the tool with Drive client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "drive_client", drive_client)

    def _run(self, file_id: str, content: str) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, file_id: str, content: str) -> str:
        """Update a file in Google Drive."""
        try:
            file_result = await self.drive_client.update_file_content(
                file_id=file_id,
                content=content
            )

            file_name = file_result.get("name", "Unknown")
            web_link = file_result.get("webViewLink", "")
            modified_time = file_result.get("modifiedTime", "")

            result = f"File updated successfully!\n"
            result += f"- Name: {file_name}\n"
            result += f"- File ID: {file_id}\n"
            if modified_time:
                result += f"- Modified: {modified_time}\n"
            if web_link:
                result += f"- Link: {web_link}"

            return result

        except DriveAPIError as e:
            return handle_tool_error(e, "Drive")
        except Exception as e:
            logger.error(
                f"Unexpected error updating Drive file: {e}", exc_info=True)
            return f"Error updating file: {str(e)}"


class DeleteDriveFileInput(BaseModel):
    """Input for deleting a Drive file."""

    file_id: str = Field(description="Google Drive file ID to delete")


class DeleteDriveFileTool(BaseTool):
    """Tool for deleting files from Google Drive."""

    name: str = "delete_drive_file"
    description: str = (
        "Delete a file from Google Drive by its file ID. "
        "WARNING: This operation is permanent and cannot be undone."
    )
    args_schema: Type[BaseModel] = DeleteDriveFileInput
    model_config = {"extra": "allow"}

    def __init__(self, drive_client: DriveClient, **kwargs):
        """Initialize the tool with Drive client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "drive_client", drive_client)

    def _run(self, file_id: str) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, file_id: str) -> str:
        """Delete a file from Google Drive."""
        try:
            await self.drive_client.delete_file(file_id)
            return f"File {file_id} deleted successfully."

        except DriveAPIError as e:
            return handle_tool_error(e, "Drive")
        except Exception as e:
            logger.error(
                f"Unexpected error deleting Drive file: {e}", exc_info=True)
            return f"Error deleting file: {str(e)}"


class CreateDriveFolderInput(BaseModel):
    """Input for creating a Drive folder."""

    name: str = Field(description="Folder name")
    parent_folder_id: Optional[str] = Field(
        default=None,
        description="Optional parent folder ID"
    )


class CreateDriveFolderTool(BaseTool):
    """Tool for creating folders in Google Drive."""

    name: str = "create_drive_folder"
    description: str = (
        "Create a new folder in Google Drive. "
        "Returns the created folder's ID, name, and link."
    )
    args_schema: Type[BaseModel] = CreateDriveFolderInput
    model_config = {"extra": "allow"}

    def __init__(self, drive_client: DriveClient, **kwargs):
        """Initialize the tool with Drive client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "drive_client", drive_client)

    def _run(self, name: str, parent_folder_id: Optional[str] = None) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, name: str, parent_folder_id: Optional[str] = None) -> str:
        """Create a folder in Google Drive."""
        try:
            folder_result = await self.drive_client.create_folder(
                name=name,
                parent_folder_id=parent_folder_id
            )

            folder_id = folder_result.get("id", "unknown")
            folder_name = folder_result.get("name", name)
            web_link = folder_result.get("webViewLink", "")

            result = f"Folder created successfully!\n"
            result += f"- Name: {folder_name}\n"
            result += f"- Folder ID: {folder_id}\n"
            if web_link:
                result += f"- Link: {web_link}"

            return result

        except DriveAPIError as e:
            return handle_tool_error(e, "Drive")
        except Exception as e:
            logger.error(
                f"Unexpected error creating Drive folder: {e}", exc_info=True)
            return f"Error creating folder: {str(e)}"


class GenerateFormattedDocumentInput(BaseModel):
    """Input for generating a formatted document."""

    name: str = Field(description="Document name")
    content: str = Field(
        description="Document content. Can be plain text or Markdown-formatted (supports # headings, **bold**, *italic*, lists)"
    )
    folder_id: Optional[str] = Field(
        default=None,
        description="Optional parent folder ID"
    )
    format_markdown: bool = Field(
        default=True,
        description="Whether to parse Markdown formatting (headings, bold, lists, etc.)"
    )


class GenerateFormattedDocumentTool(BaseTool):
    """Tool for creating formatted Google Docs with Markdown support."""

    name: str = "generate_formatted_document"
    description: str = (
        "Create a formatted Google Doc with Markdown-style formatting. "
        "Supports: # headings (##, ###, etc.), **bold**, *italic*, bullet lists (- item), numbered lists (1. item). "
        "Returns the created document's ID, name, and link."
    )
    args_schema: Type[BaseModel] = GenerateFormattedDocumentInput
    model_config = {"extra": "allow"}

    def __init__(self, drive_client: DriveClient, **kwargs):
        """Initialize the tool with Drive client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "drive_client", drive_client)

    def _run(
        self,
        name: str,
        content: str,
        folder_id: Optional[str] = None,
        format_markdown: bool = True,
    ) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(
        self,
        name: str,
        content: str,
        folder_id: Optional[str] = None,
        format_markdown: bool = True,
    ) -> str:
        """Generate a formatted document in Google Drive."""
        try:
            file_result = await self.drive_client.create_formatted_document(
                name=name,
                content=content,
                folder_id=folder_id,
                format_markdown=format_markdown,
            )

            file_id = file_result.get("id", "unknown")
            file_name = file_result.get("name", name)
            web_link = file_result.get("webViewLink", "")

            result = f"Formatted document created successfully!\n"
            result += f"- Name: {file_name}\n"
            result += f"- File ID: {file_id}\n"
            if web_link:
                result += f"- Link: {web_link}\n"
            if format_markdown:
                result += f"\nMarkdown formatting has been applied (headings, bold, lists, etc.)"

            return result

        except DriveAPIError as e:
            error_msg = handle_tool_error(e, "Drive")
            # Add helpful message about re-authorization for scope errors
            if "insufficient authentication scopes" in str(e).lower() or "insufficient permission" in str(e).lower():
                error_msg += "\n\nNote: You need to re-authorize your Google OAuth integration to grant Drive file creation permissions. Please disconnect and reconnect your Google integration."
            return error_msg
        except Exception as e:
            logger.error(
                f"Unexpected error generating formatted document: {e}", exc_info=True)
            error_msg = f"Error generating formatted document: {str(e)}"
            if "insufficient" in str(e).lower() and ("scope" in str(e).lower() or "permission" in str(e).lower()):
                error_msg += "\n\nNote: You may need to re-authorize your Google OAuth integration to grant the required Drive permissions."
            return error_msg


async def get_drive_tools(db, user_id: str) -> list[BaseTool]:
    """Get all Drive tools for a user."""
    from src.integrations.drive.client import DriveClient

    drive_client = await IntegrationService.get_drive_client(db, user_id)

    if not drive_client:
        return []  # No Drive integration available

    # Get calendar client (required for transcript matching)
    calendar_client = await IntegrationService.get_calendar_client(db, user_id)

    tools = [
        ListTranscriptFilesTool(drive_client),
        ReadTranscriptFileTool(drive_client),
        CreateDriveFileTool(drive_client),
        UpdateDriveFileTool(drive_client),
        DeleteDriveFileTool(drive_client),
        CreateDriveFolderTool(drive_client),
        GenerateFormattedDocumentTool(drive_client),
    ]

    # Add ReadMeetingTranscriptTool only if Calendar is available
    if calendar_client:
        tools.append(ReadMeetingTranscriptTool(drive_client, calendar_client))
    else:
        logger.warning(
            "Calendar integration not available - read_meeting_transcript tool will not be available")

    return tools
