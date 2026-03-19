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
                channel = discord.utils.get(
                    self.bot.guilds[0].text_channels, name=settings.discord_channel
                )
                logger.info("Connected to channel %s", channel)
                await channel.send(settings.bot_greeting)
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

                # Run RAG in a thread executor to avoid blocking the event loop
                # (blocking causes Discord heartbeat timeouts and reconnects)
                loop = asyncio.get_running_loop()
                rag_task = asyncio.ensure_future(
                    loop.run_in_executor(
                        None,
                        lambda: RAG_query(clean_message, user_id=user_id)["answer"],
                    )
                )

                # Send thinking indicator and keepalive signals while waiting for RAG.
                # First timeout sends a visible message; subsequent ones use typing
                # indicator to stay connected without cluttering the channel.
                thinking = False
                while not rag_task.done():
                    done, _ = await asyncio.wait({rag_task}, timeout=THINKING_INTERVAL)
                    if done:
                        break
                    if not thinking:
                        await message.channel.send("\U0001f914 Thinking...")
                        thinking = True
                    else:
                        await message.channel.trigger_typing()

                rag_answer = rag_task.result()
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
