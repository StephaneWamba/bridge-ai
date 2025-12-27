"""Quick test script to verify Discord token is loaded correctly."""

from src.integrations.discord.client import DiscordClient, DiscordAPIError
from src.core.config import settings
import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_discord_token():
    """Test if Discord token is loaded and working."""
    print("=" * 60)
    print("Discord Token Test")
    print("=" * 60)

    # Check if token is in settings
    token = settings.DISCORD_BOT_TOKEN
    print(f"\n[1] Checking if token is configured...")
    if not token:
        print("   ❌ ERROR: DISCORD_BOT_TOKEN is not set in environment variables")
        print("   Please check your .env file and docker-compose.yml")
        return False
    else:
        # Only show first and last few characters for security
        token_preview = f"{token[:10]}...{token[-10:]}" if len(
            token) > 20 else "***"
        print(f"   ✅ Token is configured: {token_preview}")

    # Test Discord client
    print(f"\n[2] Testing Discord API connection...")
    try:
        client = DiscordClient(bot_token=token)
        bot_info = await client.get_bot_user()

        print(f"   ✅ Successfully connected to Discord API!")
        print(f"   Bot ID: {bot_info.get('id', 'unknown')}")
        print(f"   Bot Username: {bot_info.get('username', 'unknown')}")
        print(
            f"   Bot Discriminator: {bot_info.get('discriminator', 'unknown')}")

        return True
    except DiscordAPIError as e:
        print(f"   ❌ Discord API Error: {str(e)}")
        if "401" in str(e) or "Unauthorized" in str(e):
            print("   This usually means the token is invalid or expired.")
            print("   Please regenerate the token in Discord Developer Portal.")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_discord_token())
    sys.exit(0 if result else 1)
