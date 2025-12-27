"""Discord tools for LangChain agent."""

from typing import Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.integrations.discord.client import DiscordClient, DiscordAPIError
from src.services.integration_service import IntegrationService
from src.agent.tools.base import handle_tool_error
from src.core.logging import logger


class SendDiscordMessageInput(BaseModel):
    """Input for sending a Discord message."""

    channel_id: str = Field(description="Discord channel ID (snowflake string)")
    message: str = Field(description="Message content to send")


class SendDiscordMessageTool(BaseTool):
    """Tool for sending messages to Discord channels."""

    name: str = "send_discord_message"
    description: str = (
        "Send a message to a Discord channel. Requires channel_id and message content. "
        "The channel_id is a Discord snowflake ID (numeric string) that identifies the channel."
    )
    args_schema: Type[BaseModel] = SendDiscordMessageInput
    model_config = {"extra": "allow"}  # Allow extra fields like 'client'

    def __init__(self, client: DiscordClient, **kwargs):
        """Initialize the tool with a Discord client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "client", client)

    def _run(self, channel_id: str, message: str) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError("This tool is async-only. Use _arun instead.")

    async def _arun(self, channel_id: str, message: str) -> str:
        """Send a message to a Discord channel."""
        try:
            result = await self.client.send_message(channel_id=channel_id, content=message)
            message_id = result.get("id", "unknown")
            channel_id_result = result.get("channel_id", channel_id)
            return f"Discord message sent successfully! Channel ID: {channel_id_result}, Message ID: {message_id}"
        except DiscordAPIError as e:
            return handle_tool_error(e, "Discord")
        except Exception as e:
            logger.error(f"Unexpected error sending Discord message: {e}", exc_info=True)
            return f"Error sending Discord message: {str(e)}"


class ReadDiscordMessagesInput(BaseModel):
    """Input for reading Discord messages."""

    channel_id: str = Field(description="Discord channel ID (snowflake string)")
    limit: int = Field(
        default=50, description="Maximum number of messages to return (1-100, default: 50)"
    )


class ReadDiscordMessagesTool(BaseTool):
    """Tool for reading messages from Discord channels."""

    name: str = "read_discord_messages"
    description: str = (
        "Read messages from a Discord channel. Returns recent messages with author, content, and timestamp. "
        "Requires channel_id. Optionally specify limit (1-100, default: 50) for number of messages to retrieve."
    )
    args_schema: Type[BaseModel] = ReadDiscordMessagesInput
    model_config = {"extra": "allow"}

    def __init__(self, client: DiscordClient, **kwargs):
        """Initialize the tool with a Discord client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "client", client)

    def _run(self, channel_id: str, limit: int = 50) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError("This tool is async-only. Use _arun instead.")

    async def _arun(self, channel_id: str, limit: int = 50) -> str:
        """Read messages from a Discord channel."""
        try:
            messages = await self.client.get_messages(channel_id=channel_id, limit=limit)

            if not messages:
                return f"No messages found in Discord channel {channel_id}."

            formatted = []
            for msg in messages:
                author = msg.get("author", {})
                author_name = author.get("username", "Unknown")
                author_id = author.get("id", "unknown")
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                message_id = msg.get("id", "unknown")

                formatted.append(
                    f"- Author: {author_name} ({author_id})\n"
                    f"  Message ID: {message_id}\n"
                    f"  Timestamp: {timestamp}\n"
                    f"  Content: {content[:200]}{'...' if len(content) > 200 else ''}"
                )

            return f"Found {len(messages)} message(s) in Discord channel {channel_id}:\n\n" + "\n\n".join(
                formatted
            )
        except DiscordAPIError as e:
            return handle_tool_error(e, "Discord")
        except Exception as e:
            logger.error(
                f"Unexpected error reading Discord messages: {e}", exc_info=True
            )
            return f"Error reading Discord messages: {str(e)}"


class ListDiscordChannelsInput(BaseModel):
    """Input for listing Discord channels."""

    guild_id: str = Field(
        description="Discord guild (server) ID (snowflake string)"
    )


class ListDiscordChannelsTool(BaseTool):
    """Tool for listing channels in a Discord guild."""

    name: str = "list_discord_channels"
    description: str = (
        "List channels in a Discord guild (server). Returns channel IDs, names, and types. "
        "Requires guild_id (Discord server ID). This is useful to find channel_ids for sending messages."
    )
    args_schema: Type[BaseModel] = ListDiscordChannelsInput
    model_config = {"extra": "allow"}

    def __init__(self, client: DiscordClient, **kwargs):
        """Initialize the tool with a Discord client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "client", client)

    def _run(self, guild_id: str) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError("This tool is async-only. Use _arun instead.")

    async def _arun(self, guild_id: str) -> str:
        """List channels in a Discord guild."""
        try:
            channels = await self.client.list_channels(guild_id=guild_id)

            if not channels:
                return f"No channels found in Discord guild {guild_id}."

            formatted = []
            for channel in channels:
                channel_id = channel.get("id", "unknown")
                channel_name = channel.get("name", "Unknown")
                channel_type = channel.get("type", 0)
                # Discord channel types: 0 = text, 2 = voice, 4 = category, etc.
                type_names = {0: "text", 2: "voice", 4: "category", 5: "announcement"}
                type_name = type_names.get(channel_type, f"type_{channel_type}")

                formatted.append(
                    f"- Channel: {channel_name}\n"
                    f"  ID: {channel_id}\n"
                    f"  Type: {type_name}"
                )

            return f"Found {len(channels)} channel(s) in Discord guild {guild_id}:\n\n" + "\n\n".join(
                formatted
            )
        except DiscordAPIError as e:
            return handle_tool_error(e, "Discord")
        except Exception as e:
            logger.error(
                f"Unexpected error listing Discord channels: {e}", exc_info=True
            )
            return f"Error listing Discord channels: {str(e)}"


async def get_discord_tools(db, user_id: str) -> list[BaseTool]:
    """Get all Discord tools for a user."""
    client = await IntegrationService.get_discord_client(db, user_id)

    if not client:
        return []  # No Discord integration connected

    return [
        SendDiscordMessageTool(client),
        ReadDiscordMessagesTool(client),
        ListDiscordChannelsTool(client),
    ]

