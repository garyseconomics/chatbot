import logging

import discord
from discord.ext import commands

from config import settings
from rag.rag_manager import RAG_query

logger = logging.getLogger(__name__)


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

    def _setup_bot(self):
        @self.bot.event
        async def on_ready():
            logger.info("Bot connected as %s - %s", self.bot.user.name, self.bot.user.id)
            channel = discord.utils.get(
                self.bot.guilds[0].text_channels, name=settings.discord_channel
            )
            logger.info("Connected to channel %s", channel)
            await channel.send(settings.bot_greeting)

        @self.bot.event
        async def on_message(message):
            # The bot  ignores its own messages
            if message.author == self.bot.user:
                return
            # The bot answers when it is mentioned
            if self.bot.user in message.mentions:
                bot_id = str(self.bot.user.id)
                # Eliminates the bot mention from the message
                clean_message = message.content.lstrip("<@" + bot_id + "> ")
                logger.debug("Message received: %s", clean_message)
                rag_answer = RAG_query(clean_message)["answer"]
                logger.debug("RAG answer: %s", rag_answer)
                channel = discord.utils.get(
                    self.bot.guilds[0].text_channels, name=settings.discord_channel
                )
                await channel.send(rag_answer)

    def run(self):
        logger.info("Connecting Discord...")
        self.bot.run(self.discord_token)


discord_client = DiscordClient()
discord_client.run()
