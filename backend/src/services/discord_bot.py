"""Discord bot service that listens for messages and forwards them to BridgeAI agent."""

import asyncio
import re
import discord
from discord.ext import commands
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSession as AsyncSessionType
from uuid import UUID

from src.core.config import settings
from src.core.database import AsyncSessionLocal
from src.core.logging import logger
from src.agent.orchestrator import AgentOrchestrator
from src.services.conversation_service import ConversationService
from src.models.user import User
from sqlalchemy import select


def format_discord_message(text: str) -> str:
    """Format text for Discord with proper escape sequence handling.

    Args:
        text: Raw text that may contain escape sequences like \\n, \\t, etc.

    Returns:
        Formatted text with escape sequences decoded and cleaned up.
    """
    if not text:
        return "No response generated."

    # Decode escape sequences (\n -> actual newline, \t -> tab, etc.)
    try:
        # Use encode/decode trick to handle all escape sequences
        # This converts literal \n to actual newline character
        text = text.encode('utf-8').decode('unicode_escape')
    except (UnicodeDecodeError, UnicodeError) as e:
        # Fallback: manually replace common escape sequences
        logger.warning(
            f"Failed to decode escape sequences, using fallback: {e}")
        text = text.replace('\\n', '\n')
        text = text.replace('\\t', '\t')
        text = text.replace('\\r', '\r')

    # Clean up excessive newlines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove trailing whitespace from each line
    lines = text.split('\n')
    text = '\n'.join(line.rstrip() for line in lines)

    # Trim overall whitespace
    text = text.strip()

    return text


class DiscordBot:
    """Discord bot that listens for messages and processes them with BridgeAI agent."""

    def __init__(self):
        """Initialize Discord bot."""
        self.bot_token = settings.DISCORD_BOT_TOKEN
        self.intents = discord.Intents.default()
        self.intents.message_content = True  # Required to read message content
        self.intents.messages = True
        self.bot = commands.Bot(command_prefix="!", intents=self.intents)
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup bot event handlers."""

        @self.bot.event
        async def on_ready():
            """Called when bot is ready."""
            logger.info(f"Discord bot logged in as {self.bot.user}")

        @self.bot.event
        async def on_message(message: discord.Message):
            """Handle incoming messages."""
            logger.info(
                f"Discord message received: {message.content[:100]} from {message.author} in {message.channel}")

            # Ignore messages from the bot itself
            if message.author == self.bot.user:
                logger.debug("Ignoring message from bot itself")
                return

            # Only respond to messages that mention the bot or are in DMs
            if isinstance(message.channel, discord.DMChannel):
                # Always respond in DMs
                logger.info("Processing DM message")
                await self._process_message(message)
            elif self.bot.user in message.mentions:
                # Respond when mentioned in a channel
                logger.info("Processing mentioned message in channel")
                await self._process_message(message)
            else:
                # Process commands normally
                logger.debug(
                    "Message doesn't mention bot, processing as command")
                await self.bot.process_commands(message)

    async def _process_message(self, message: discord.Message):
        """Process a Discord message through BridgeAI agent."""
        try:
            # Show typing indicator
            async with message.channel.typing():
                # Get user from database (for now, use first active user or create a mapping)
                # In production, you'd want to map Discord user IDs to BridgeAI user IDs
                async with AsyncSessionLocal() as db_session:
                    try:
                        # Get the first active user (or implement proper user mapping)
                        result = await db_session.execute(
                            select(User).where(User.is_active == True).limit(1)
                        )
                        user = result.scalar_one_or_none()

                        if not user:
                            await message.channel.send(
                                "❌ No active users found. Please sign up at the BridgeAI web interface first."
                            )
                            return

                        # Remove bot mention from message content
                        content = message.content
                        if self.bot.user in message.mentions:
                            # Remove @bot mentions
                            content = content.replace(
                                f"<@{self.bot.user.id}>", "").strip()
                            content = content.replace(
                                f"<@!{self.bot.user.id}>", "").strip()

                        if not content:
                            await message.channel.send(
                                "👋 Hi! I'm BridgeAI. Ask me anything about your business tools (HubSpot, Gmail, Calendar, etc.) or send me a command!"
                            )
                            return

                        # Create or get conversation session for this Discord channel
                        # Use channel ID as session identifier
                        session_id = f"discord_{message.channel.id}"

                        # Process message through BridgeAI agent
                        orchestrator = AgentOrchestrator()
                        response_dict = await orchestrator.process_message(
                            message=content,
                            session_id=session_id,
                            user_id=str(user.id),
                            db=db_session,
                        )

                        # Extract response text from dictionary
                        response_text = response_dict.get(
                            'response', 'No response generated.')

                        # Format the response (decode escape sequences, clean up)
                        formatted_text = format_discord_message(response_text)

                        # Send response back to Discord
                        # Discord has a 2000 character limit per message
                        if len(formatted_text) > 2000:
                            # Split into chunks (respecting newlines when possible)
                            chunks = []
                            current_chunk = ""

                            for line in formatted_text.split('\n'):
                                # If adding this line would exceed limit, save current chunk
                                if len(current_chunk) + len(line) + 1 > 2000:
                                    if current_chunk:
                                        chunks.append(current_chunk)
                                    # If single line is too long, split it
                                    if len(line) > 2000:
                                        # Split long line into 2000-char chunks
                                        for i in range(0, len(line), 2000):
                                            chunks.append(line[i:i+2000])
                                        current_chunk = ""
                                    else:
                                        current_chunk = line + '\n'
                                else:
                                    current_chunk += line + '\n'

                            # Add remaining chunk
                            if current_chunk:
                                chunks.append(current_chunk.strip())

                            # Send all chunks
                            for chunk in chunks:
                                if chunk:  # Only send non-empty chunks
                                    await message.channel.send(chunk)
                        else:
                            await message.channel.send(formatted_text)

                    except Exception as e:
                        await db_session.rollback()
                        raise

        except Exception as e:
            logger.error(
                f"Error processing Discord message: {e}", exc_info=True)
            try:
                await message.channel.send(
                    f"❌ Sorry, I encountered an error: {str(e)}"
                )
            except Exception as send_error:
                logger.error(
                    f"Error sending error message to Discord: {send_error}", exc_info=True)

    async def start(self):
        """Start the Discord bot."""
        if not self.bot_token:
            logger.warning(
                "DISCORD_BOT_TOKEN not set. Discord bot will not start.")
            return

        try:
            await self.bot.start(self.bot_token)
        except discord.LoginFailure:
            logger.error(
                "Failed to login to Discord. Check your DISCORD_BOT_TOKEN.")
        except Exception as e:
            logger.error(f"Error starting Discord bot: {e}", exc_info=True)

    async def close(self):
        """Close the Discord bot."""
        await self.bot.close()


# Global bot instance
_discord_bot: Optional[DiscordBot] = None


async def start_discord_bot():
    """Start the Discord bot in the background."""
    global _discord_bot

    if not settings.DISCORD_BOT_TOKEN:
        logger.info("DISCORD_BOT_TOKEN not set. Skipping Discord bot startup.")
        return

    _discord_bot = DiscordBot()

    # Run bot in background task
    asyncio.create_task(_discord_bot.start())
    logger.info("Discord bot startup task created.")


async def stop_discord_bot():
    """Stop the Discord bot."""
    global _discord_bot

    if _discord_bot:
        await _discord_bot.close()
        _discord_bot = None
        logger.info("Discord bot stopped.")
