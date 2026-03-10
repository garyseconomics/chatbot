from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# The discord bot registers event handlers (on_message, on_ready) as closures inside
# DiscordClient._setup_bot() via the @self.bot.event decorator. To test them, we mock
# commands.Bot so that @bot.event captures the handler functions into a dict, then we
# call those handlers directly with mock messages.


@pytest.fixture
def discord_bot():
    """Create a DiscordClient with mocked dependencies, capturing event handlers."""
    handlers = {}
    mock_bot = MagicMock()
    mock_bot.user = MagicMock()
    mock_bot.user.id = 12345
    mock_bot.user.name = "TestBot"

    # Replace @bot.event with a decorator that stores handlers by name
    # so we can call them directly in tests (e.g. handlers["on_message"])
    def capture_event(func):
        handlers[func.__name__] = func
        return func

    mock_bot.event = capture_event

    mock_settings = MagicMock()
    mock_settings.discord_token = "fake-token"
    mock_settings.discord_channel = "general"
    mock_settings.bot_greeting = "Hello!"

    with (
        patch("discord.ext.commands.Bot", return_value=mock_bot),
        patch("discord.Intents"),
        patch("interfaces.discord_bot.settings", mock_settings),
    ):
        from interfaces.discord_bot import DiscordClient

        client = DiscordClient()

    return {
        "handlers": handlers,
        "bot": mock_bot,
        "client": client,
        "settings": mock_settings,
    }


def _make_message(author, mentions=None, content="test message"):
    """Create a mock discord Message."""
    message = MagicMock()
    message.author = author
    message.mentions = mentions or []
    message.content = content
    return message


# --- on_message: basic behavior ---


@pytest.mark.asyncio
async def test_bot_ignores_own_messages(discord_bot):
    """The bot should not respond to its own messages to avoid infinite loops."""
    on_message = discord_bot["handlers"]["on_message"]
    bot = discord_bot["bot"]

    # Send a message authored by the bot itself
    message = _make_message(author=bot.user, content="hello")

    with patch("interfaces.discord_bot.RAG_query") as mock_rag:
        await on_message(message)
        # RAG should never be called for the bot's own messages
        mock_rag.assert_not_called()


@pytest.mark.asyncio
async def test_bot_ignores_messages_without_mention(discord_bot):
    """The bot only responds when explicitly @mentioned."""
    on_message = discord_bot["handlers"]["on_message"]

    other_user = MagicMock()
    # Message from another user, but without mentioning the bot
    message = _make_message(author=other_user, mentions=[], content="hello everyone")

    with patch("interfaces.discord_bot.RAG_query") as mock_rag:
        await on_message(message)
        mock_rag.assert_not_called()


@pytest.mark.asyncio
async def test_bot_responds_when_mentioned(discord_bot):
    """When @mentioned, the bot queries RAG and sends the answer to the channel."""
    on_message = discord_bot["handlers"]["on_message"]
    bot = discord_bot["bot"]

    mock_channel = AsyncMock()
    bot.guilds = [MagicMock()]

    with (
        patch(
            "interfaces.discord_bot.RAG_query",
            return_value={"answer": "The economy is complex.", "context": [], "question": "How?"},
        ),
        patch("interfaces.discord_bot.discord.utils.get", return_value=mock_channel),
    ):
        other_user = MagicMock()
        message = _make_message(
            author=other_user,
            mentions=[bot.user],
            content=f"<@{bot.user.id}> How is the economy?",
        )
        await on_message(message)

    mock_channel.send.assert_called_once_with("The economy is complex.")


# --- on_message: error handling ---
# The handler catches exceptions, logs them, and sends a fallback error message
# to the user via message.channel (which always works, even if the channel lookup failed).


@pytest.mark.asyncio
async def test_bot_sends_error_message_when_channel_not_found(discord_bot):
    """When discord.utils.get returns None (channel name doesn't match), the handler
    catches the error and replies via message.channel with an error message."""
    on_message = discord_bot["handlers"]["on_message"]
    bot = discord_bot["bot"]

    bot.guilds = [MagicMock()]

    with (
        patch(
            "interfaces.discord_bot.RAG_query",
            return_value={"answer": "Answer", "context": [], "question": "Q"},
        ),
        # Simulate channel not found
        patch("interfaces.discord_bot.discord.utils.get", return_value=None),
    ):
        other_user = MagicMock()
        message = _make_message(
            author=other_user,
            mentions=[bot.user],
            content=f"<@{bot.user.id}> question",
        )
        # message.channel.send needs to be async
        message.channel = AsyncMock()
        await on_message(message)

    # The bot should reply with an error message via message.channel
    message.channel.send.assert_called_once()
    error_msg = message.channel.send.call_args[0][0]
    assert "sorry" in error_msg.lower()


@pytest.mark.asyncio
async def test_bot_sends_error_message_when_send_fails(discord_bot):
    """When channel.send() raises (e.g. Discord API error), the handler catches it
    and sends a fallback error message via message.channel."""
    on_message = discord_bot["handlers"]["on_message"]
    bot = discord_bot["bot"]

    mock_channel = AsyncMock()
    mock_channel.send.side_effect = Exception("Discord API error")
    bot.guilds = [MagicMock()]

    with (
        patch(
            "interfaces.discord_bot.RAG_query",
            return_value={"answer": "Answer", "context": [], "question": "Q"},
        ),
        patch("interfaces.discord_bot.discord.utils.get", return_value=mock_channel),
    ):
        other_user = MagicMock()
        message = _make_message(
            author=other_user,
            mentions=[bot.user],
            content=f"<@{bot.user.id}> question",
        )
        # message.channel.send is the fallback — must be a different mock than the
        # failing channel.send
        message.channel = AsyncMock()
        await on_message(message)

    message.channel.send.assert_called_once()
    error_msg = message.channel.send.call_args[0][0]
    assert "sorry" in error_msg.lower()


# --- on_ready ---


@pytest.mark.asyncio
async def test_on_ready_sends_greeting(discord_bot):
    """On startup, the bot sends the configured greeting to the configured channel."""
    on_ready = discord_bot["handlers"]["on_ready"]
    bot = discord_bot["bot"]

    mock_channel = AsyncMock()
    bot.guilds = [MagicMock()]

    with (
        patch("interfaces.discord_bot.discord.utils.get", return_value=mock_channel),
        patch("interfaces.discord_bot.settings", discord_bot["settings"]),
    ):
        await on_ready()

    mock_channel.send.assert_called_once_with("Hello!")


@pytest.mark.asyncio
async def test_on_ready_logs_error_when_channel_not_found(discord_bot):
    """If the configured channel doesn't exist, on_ready catches the error and logs it
    instead of crashing the bot."""
    on_ready = discord_bot["handlers"]["on_ready"]
    bot = discord_bot["bot"]

    bot.guilds = [MagicMock()]

    with patch("interfaces.discord_bot.discord.utils.get", return_value=None):
        # Should not raise — the error is caught and logged
        await on_ready()
