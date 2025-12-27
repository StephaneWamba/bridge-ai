"""Gmail tools for LangChain agent."""

from typing import Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.integrations.gmail.client import GmailClient, GmailAPIError
from src.services.integration_service import IntegrationService
from src.agent.tools.base import handle_tool_error
from src.core.logging import logger


class ReadGmailEmailsInput(BaseModel):
    """Input for reading Gmail emails."""

    query: Optional[str] = Field(
        default="", description="Gmail search query (e.g., 'from:example@gmail.com', 'subject:meeting')"
    )
    limit: int = Field(
        default=10, description="Maximum number of emails to return (1-50)")


class ReadGmailEmailsTool(BaseTool):
    """Tool for reading Gmail emails."""

    name: str = "read_gmail_emails"
    description: str = (
        "Read Gmail emails based on a search query. "
        "Returns a list of emails with subject, sender, and snippet. "
        "Use Gmail search syntax (e.g., 'from:example@gmail.com', 'subject:meeting', 'is:unread')."
    )
    args_schema: Type[BaseModel] = ReadGmailEmailsInput
    model_config = {"extra": "allow"}  # Allow extra fields like 'client'

    def __init__(self, client: GmailClient, **kwargs):
        """Initialize the tool with a Gmail client."""
        super().__init__(**kwargs)
        # Use object.__setattr__ for Pydantic v2
        object.__setattr__(self, "client", client)

    def _run(self, query: str = "", limit: int = 10) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, query: str = "", limit: int = 10) -> str:
        """Read emails from Gmail."""
        try:
            messages = await self.client.list_messages(query=query, limit=min(limit, 50))

            if not messages:
                return "No emails found matching the query."

            # Get full message details for each
            formatted = []
            for msg in messages[:limit]:
                try:
                    full_msg = await self.client.get_message(msg["id"])
                    payload = full_msg.get("payload", {})
                    # Headers can be a list or dict depending on message format
                    headers = payload.get("headers", [])
                    if isinstance(headers, dict):
                        # Convert dict to list format
                        headers = [{"name": k, "value": v}
                                   for k, v in headers.items()]

                    # Extract headers
                    subject = next(
                        (h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
                    sender = next(
                        (h["value"] for h in headers if h["name"] == "From"), "Unknown")
                    date = next(
                        (h["value"] for h in headers if h["name"] == "Date"), "Unknown")

                    snippet = full_msg.get("snippet", "")

                    message_id = msg.get("id", "unknown")
                    formatted.append(
                        f"- Subject: {subject}\n  From: {sender}\n  Date: {date}\n  Message ID: {message_id}\n  Snippet: {snippet[:100]}..."
                    )
                except Exception as e:
                    logger.warning(
                        f"Error getting full message {msg.get('id')}: {e}")
                    formatted.append(
                        f"- Message ID: {msg.get('id')} (error loading details)")

            return f"Found {len(messages)} email(s):\n" + "\n\n".join(formatted)
        except GmailAPIError as e:
            return handle_tool_error(e, "Gmail")
        except Exception as e:
            logger.error(
                f"Unexpected error reading Gmail emails: {e}", exc_info=True)
            return f"Error reading emails: {str(e)}"


class SendGmailEmailInput(BaseModel):
    """Input for sending a Gmail email."""

    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body/content")


class SendGmailEmailTool(BaseTool):
    """Tool for sending new Gmail emails (not replies)."""

    name: str = "send_gmail_email"
    description: str = (
        "Send a NEW email via Gmail (not a reply). Requires recipient email address, subject, and body. "
        "Use this for sending new emails. For replying to existing emails, use reply_gmail_email instead."
    )
    args_schema: Type[BaseModel] = SendGmailEmailInput
    model_config = {"extra": "allow"}  # Allow extra fields like 'client'

    def __init__(self, client: GmailClient, **kwargs):
        """Initialize the tool with a Gmail client."""
        super().__init__(**kwargs)
        # Use object.__setattr__ for Pydantic v2
        object.__setattr__(self, "client", client)

    def _run(self, to: str, subject: str, body: str) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, to: str, subject: str, body: str) -> str:
        """Send a new email via Gmail."""
        try:
            result = await self.client.send_message(to=to, subject=subject, body=body)
            message_id = result.get("id", "unknown")
            return f"Email sent successfully! Message ID: {message_id}"
        except GmailAPIError as e:
            return handle_tool_error(e, "Gmail")
        except Exception as e:
            logger.error(
                f"Unexpected error sending Gmail email: {e}", exc_info=True)
            return f"Error sending email: {str(e)}"


class ReplyGmailEmailInput(BaseModel):
    """Input for replying to a Gmail email."""

    message_id: str = Field(
        description="The Gmail message ID to reply to (from read_gmail_emails)")
    body: str = Field(
        description="Reply body/content (plain text only, no attachments from original will be included)")


class ReplyGmailEmailTool(BaseTool):
    """Tool for replying to Gmail emails."""

    name: str = "reply_gmail_email"
    description: str = (
        "Reply to an existing Gmail email. Requires the message_id from read_gmail_emails and reply body. "
        "IMPORTANT: This sends a plain text reply only - it does NOT include attachments from the original email. "
        "The reply will be properly threaded with the original message."
    )
    args_schema: Type[BaseModel] = ReplyGmailEmailInput
    model_config = {"extra": "allow"}  # Allow extra fields like 'client'

    def __init__(self, client: GmailClient, **kwargs):
        """Initialize the tool with a Gmail client."""
        super().__init__(**kwargs)
        # Use object.__setattr__ for Pydantic v2
        object.__setattr__(self, "client", client)

    def _run(self, message_id: str, body: str) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, message_id: str, body: str) -> str:
        """Reply to an email via Gmail."""
        try:
            # Get the original message first to extract recipient info
            original_message = await self.client.get_message(message_id)
            payload = original_message.get("payload", {})
            headers = payload.get("headers", [])
            if isinstance(headers, dict):
                headers = [{"name": k, "value": v} for k, v in headers.items()]

            original_from = next(
                (h["value"] for h in headers if h["name"] == "From"), ""
            )
            original_subject = next(
                (h["value"] for h in headers if h["name"] == "Subject"), ""
            )

            # Extract email address from "Name <email@example.com>" format
            import re
            from_match = re.search(r'<([^>]+)>', original_from)
            reply_to_email = from_match.group(
                1) if from_match else original_from.strip()
            reply_to_email = reply_to_email.strip()

            # Check for no-reply addresses and warn
            no_reply_patterns = [
                r'noreply', r'no-reply', r'do-not-reply', r'donotreply',
                r'notifications-noreply', r'notification', r'no_reply'
            ]
            email_lower = reply_to_email.lower()
            is_no_reply = any(re.search(pattern, email_lower)
                              for pattern in no_reply_patterns)

            # Send the reply
            result = await self.client.reply_to_message(
                message_id=message_id,
                body=body,
                include_attachments=False  # Never include attachments unless explicitly requested
            )
            reply_id = result.get("id", "unknown")

            warning = ""
            if is_no_reply:
                warning = f" ⚠️ Warning: {reply_to_email} appears to be a no-reply address. The email may bounce or not be monitored."

            return f"Reply sent successfully to {reply_to_email}! Subject: Re: {original_subject}. Message ID: {reply_id}.{warning}"
        except GmailAPIError as e:
            return handle_tool_error(e, "Gmail")
        except Exception as e:
            logger.error(
                f"Unexpected error replying to Gmail email: {e}", exc_info=True)
            return f"Error replying to email: {str(e)}"


async def get_gmail_tools(db, user_id: str) -> list[BaseTool]:
    """Get all Gmail tools for a user."""
    client = await IntegrationService.get_google_client(db, user_id)

    if not client:
        return []  # No Gmail integration connected

    return [
        ReadGmailEmailsTool(client),
        SendGmailEmailTool(client),
        ReplyGmailEmailTool(client),
    ]
