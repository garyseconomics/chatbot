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


class DiscordClient:
    def __init__(self) -> None:
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
            # The bot ignores its own messages
            if message.author == self.bot.user:
                return

            is_dm = message.guild is None
            is_mentioned = self.bot.user in message.mentions

            # In DMs: respond to any message. In guilds: only when @mentioned.
            if not is_dm and not is_mentioned:
                return

            try:
                # Strip the bot mention from the message if present
                bot_mention = f"<@{self.bot.user.id}>"
                clean_message = message.content.replace(bot_mention, "").strip()
                logger.debug("Message received: %s", clean_message)
                user_id = f"discord:{message.author.id}"
                rag_answer = RAG_query(clean_message, user_id=user_id)["answer"]
                logger.debug("RAG answer: %s", rag_answer)
                await message.channel.send(rag_answer)
            except Exception:
                logger.exception("Failed to handle message")
                await message.channel.send("Sorry, something went wrong. Please try again later.")

    def run(self) -> None:
        logger.info("Connecting Discord...")
        self.bot.run(self.discord_token)


if __name__ == "__main__":
    discord_client = DiscordClient()
    discord_client.run()
