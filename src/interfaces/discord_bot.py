import asyncio
import logging

# Filter third-party warnings we can't fix:
# - PyNaCl/davey not installed: discord.py voice dependencies we don't need
logging.getLogger("discord.client").addFilter(
    lambda record: "is not installed, voice will NOT be supported" not in record.getMessage()
)

import discord  # noqa: E402
from discord.ext import commands  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402

from config import settings  # noqa: E402
from interfaces.chunker import discord_bot_chunker  # noqa: E402
from orchestrator.orchestrator import answer_question  # noqa: E402

logger = logging.getLogger(__name__)

THINKING_INTERVAL = 30  # seconds between thinking indicators

# Conversation and knowledge of each channel and DM, by id (in memory only)
chat_memories = {}


def is_allowed_user(user_id) -> bool:
    if not settings.testing_mode:
        return True
    return user_id in settings.discord_allowed_user_ids


def should_respond(message, bot_user, is_dm) -> bool:
    """Decide whether the bot should respond to this message."""
    # The bot doesn't answer its own messages
    if message.author.id == bot_user.id:
        return False
    # The bot is mentioned in the configured channel
    is_mentioned = bot_user in message.mentions
    channel_name = getattr(message.channel, "name", None)
    if is_mentioned and channel_name == settings.discord_channel:
        return True
    # A direct message, and DMs are on
    if is_dm and settings.discord_dms_enabled and is_allowed_user(message.author.id):
        return True
    return False


def strip_bot_mention(content, bot_id) -> str:
    """Remove the bot's @mention from message text."""
    return content.replace(f"<@{bot_id}>", "").strip()


def get_conversation_id(message) -> int:
    """Return the id that identifies the conversation this message belongs to."""
    if message.guild:
        # Channels keep one conversation each, shared by everyone in the channel
        return message.channel.id
    # DMs keep one conversation per user
    return message.author.id


def get_chat_memory(conversation_id) -> dict:
    """Return the memory of this conversation, creating an empty one the first time."""
    return chat_memories.setdefault(conversation_id, {"conversation": [], "knowledge": {}})


async def wait_with_thinking(channel, task, interval):
    """Wait for a task to complete, sending thinking indicators periodically.

    First timeout sends a visible "Thinking..." message. Subsequent timeouts
    use typing to stay connected without cluttering the channel.
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
            await channel.typing()


async def handle_message(message, bot_user) -> None:
    """Process a user message: get the answer and send it, chunked if needed."""
    try:
        clean_message = strip_bot_mention(message.content, bot_user.id)
        logger.debug("Message received: %s", clean_message)

        chat_memory = get_chat_memory(get_conversation_id(message))
        chat_memory["conversation"].append(HumanMessage(content=clean_message))

        task = asyncio.create_task(
            answer_question(
                chat_memory["conversation"], chat_memory["knowledge"], client_type="discord"
            )
        )

        await wait_with_thinking(message.channel, task, THINKING_INTERVAL)
        answer = task.result()
        logger.debug("Answer: %s", answer)
        for chunk in discord_bot_chunker.chunk(answer):
            await message.channel.send(chunk.text)
    except Exception:
        logger.exception("Failed to handle message")
        await message.channel.send(settings.error_messages["DefaultError"])


def should_turn_away(user_id, bot_id) -> bool:
    # The bot doesn't answer its own messages
    if user_id == bot_id:
        return False
    # In testing mode, only the allowed users can use DMs
    if not is_allowed_user(user_id):
        return True
    if not settings.discord_dms_enabled:
        return True
    return False


async def turn_away(message) -> None:
    """Tell the user the bot doesn't answer their DMs, and log who they are."""
    if settings.testing_mode:
        # Logged so we can add team members to the list by hand.
        logger.warning(
            "User not allowed: id=%s name=%s username=%s",
            message.author.id,
            message.author.display_name,
            message.author.name,
        )
    await message.channel.send(settings.discord_dms_off_message)


async def process_message(message, bot_user) -> None:
    """Answer the message, turn it away or ignore it."""
    is_dm = message.guild is None
    # Answer the message if the bot should
    if should_respond(message, bot_user, is_dm):
        await handle_message(message, bot_user)
    elif is_dm and should_turn_away(message.author.id, bot_user.id):
        await turn_away(message)


async def send_greeting(text_channels):
    """Find the configured channel and send the greeting message."""
    # Channels are off
    if not settings.discord_channel:
        return
    channel = discord.utils.get(text_channels, name=settings.discord_channel)
    if channel is None:
        logger.warning(
            "Channel '%s' not found: the bot won't answer in any channel",
            settings.discord_channel,
        )
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
            await process_message(message, self.bot.user)

    def run(self):
        if settings.discord_dms_enabled is None:
            logger.warning("DISCORD_DMS_ENABLED is not set: the bot won't answer DMs")
        logger.info("Connecting Discord...")
        self.bot.run(self.discord_token)


if __name__ == "__main__":
    discord_client = DiscordClient()
    discord_client.run()
