import asyncio
import logging
import warnings

# Filter third-party warnings we can't fix:
# - RequestsDependencyWarning: chardet/urllib3 versions newer than requests expects
# - PyNaCl/davey not installed: discord.py voice dependencies we don't need
warnings.filterwarnings("ignore", message="urllib3.*doesn't match a supported version")
logging.getLogger("discord.client").addFilter(
    lambda record: "is not installed, voice will NOT be supported" not in record.getMessage()
)

import discord  # noqa: E402
from discord.ext import commands  # noqa: E402

from config import settings  # noqa: E402
from rag.rag_manager import RAG_query  # noqa: E402

logger = logging.getLogger(__name__)

THINKING_INTERVAL = 30  # seconds between thinking indicators


def should_respond(author_id, bot_id, is_dm, is_mentioned) -> bool:
    """Decide whether the bot should respond to this message."""
    if author_id == bot_id:
        return False
    if not is_dm and not is_mentioned:
        return False
    return True


def strip_bot_mention(content, bot_id) -> str:
    """Remove the bot's @mention from message text."""
    return content.replace(f"<@{bot_id}>", "").strip()


async def wait_with_thinking(channel, task, interval):
    """Wait for a task to complete, sending thinking indicators periodically.

    First timeout sends a visible "Thinking..." message. Subsequent timeouts
    use trigger_typing to stay connected without cluttering the channel.
    """
    thinking = False
    while not task.done():
        done, _ = await asyncio.wait({task}, timeout=interval)
        if done:
            break
        if not thinking:
            await channel.send("\U0001f914 Thinking...")
            thinking = True
        else:
            await channel.trigger_typing()


async def send_greeting(text_channels):
    """Find the configured channel and send the greeting message."""
    channel = discord.utils.get(text_channels, name=settings.discord_channel_for_bot_greeting)
    if channel is None:
        logger.error("Channel '%s' not found", settings.discord_channel_for_bot_greeting)
        return
    await channel.send(settings.bot_greeting)


class DiscordClient:
    def __init__(self):
        # Token to connect to discord server
        self.discord_token = settings.discord_token
        # This makes the bot answer to !botname
        self.discordbot_prefix = "!"
        # Setting access permissions
        self.discordintents = discord.Intents.default()
        self.discordintents.messages = True
        self.discordintents.message_content = True
        # Creates the bot instance
        self.bot = commands.Bot(command_prefix=self.discordbot_prefix, intents=self.discordintents)
        # Setup the bot
        self._setup_bot()

    def _setup_bot(self) -> None:
        @self.bot.event
        async def on_ready():
            try:
                logger.info("Bot connected as %s - %s", self.bot.user.name, self.bot.user.id)
                await send_greeting(self.bot.guilds[0].text_channels)
            except Exception:
                logger.exception("Failed during on_ready")

        @self.bot.event
        async def on_message(message):
            if not should_respond(
                author_id=message.author.id,
                bot_id=self.bot.user.id,
                is_dm=message.guild is None,
                is_mentioned=self.bot.user in message.mentions,
            ):
                return

            try:
                clean_message = strip_bot_mention(message.content, self.bot.user.id)
                logger.debug("Message received: %s", clean_message)
                user_id = f"discord:{message.author.id}"

                # RAG_query is async, so we can use create_task directly
                rag_task = asyncio.create_task(
                    RAG_query(clean_message, user_id=user_id)
                )

                await wait_with_thinking(message.channel, rag_task, THINKING_INTERVAL)
                rag_answer = rag_task.result()["answer"]
                logger.debug("RAG answer: %s", rag_answer)
                await message.channel.send(rag_answer)
            except Exception:
                logger.exception("Failed to handle message")
                await message.channel.send("Sorry, something went wrong. Please try again later.")

    def run(self):
        logger.info("Connecting Discord...")
        self.bot.run(self.discord_token)


if __name__ == "__main__":
    discord_client = DiscordClient()
    discord_client.run()
