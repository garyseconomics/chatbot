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


def _make_message(author, mentions=None, content="test message", guild=MagicMock()):
    """Create a mock discord Message. guild=None simulates a DM."""
    message = MagicMock()
    message.author = author
    message.mentions = mentions or []
    message.content = content
    message.guild = guild
    message.channel = AsyncMock()
    return message


# --- on_message: guild channel behavior ---


@pytest.mark.asyncio
async def test_bot_ignores_own_messages(discord_bot):
    """The bot should not respond to its own messages to avoid infinite loops."""
    on_message = discord_bot["handlers"]["on_message"]
    bot = discord_bot["bot"]

    message = _make_message(author=bot.user, content="hello")

    with patch("interfaces.discord_bot.RAG_query") as mock_rag:
        await on_message(message)
        mock_rag.assert_not_called()


@pytest.mark.asyncio
async def test_bot_ignores_guild_messages_without_mention(discord_bot):
    """In guild channels, the bot only responds when explicitly @mentioned."""
    on_message = discord_bot["handlers"]["on_message"]

    other_user = MagicMock()
    message = _make_message(author=other_user, mentions=[], content="hello everyone")

    with patch("interfaces.discord_bot.RAG_query") as mock_rag:
        await on_message(message)
        mock_rag.assert_not_called()


@pytest.mark.asyncio
async def test_bot_responds_when_mentioned_in_guild(discord_bot):
    """When @mentioned in a guild channel, the bot queries RAG and replies
    in the same channel."""
    on_message = discord_bot["handlers"]["on_message"]
    bot = discord_bot["bot"]

    other_user = MagicMock()
    message = _make_message(
        author=other_user,
        mentions=[bot.user],
        content=f"<@{bot.user.id}> How is the economy?",
    )

    with patch(
        "interfaces.discord_bot.RAG_query",
        return_value={"answer": "The economy is complex.", "context": [], "question": "How?"},
    ):
        await on_message(message)

    message.channel.send.assert_called_once_with("The economy is complex.")


# --- on_message: DM behavior ---


@pytest.mark.asyncio
async def test_bot_responds_to_dm_without_mention(discord_bot):
    """In DMs, the bot responds to any message without requiring an @mention."""
    on_message = discord_bot["handlers"]["on_message"]

    other_user = MagicMock()
    message = _make_message(
        author=other_user,
        mentions=[],
        content="What causes inflation?",
        guild=None,
    )

    with patch(
        "interfaces.discord_bot.RAG_query",
        return_value={"answer": "Inflation is caused by...", "context": [], "question": "Q"},
    ):
        await on_message(message)

    message.channel.send.assert_called_once_with("Inflation is caused by...")


@pytest.mark.asyncio
async def test_bot_ignores_own_dm(discord_bot):
    """The bot should not respond to its own messages even in DMs."""
    on_message = discord_bot["handlers"]["on_message"]
    bot = discord_bot["bot"]

    message = _make_message(author=bot.user, content="hello", guild=None)

    with patch("interfaces.discord_bot.RAG_query") as mock_rag:
        await on_message(message)
        mock_rag.assert_not_called()


@pytest.mark.asyncio
async def test_dm_strips_bot_mention_if_present(discord_bot):
    """If a user @mentions the bot in a DM, the mention is stripped from the question."""
    on_message = discord_bot["handlers"]["on_message"]
    bot = discord_bot["bot"]

    other_user = MagicMock()
    message = _make_message(
        author=other_user,
        mentions=[bot.user],
        content=f"<@{bot.user.id}> What is GDP?",
        guild=None,
    )

    with patch("interfaces.discord_bot.RAG_query") as mock_rag:
        mock_rag.return_value = {"answer": "GDP is...", "context": [], "question": "Q"}
        await on_message(message)
        # The question passed to RAG should not contain the mention
        question_arg = mock_rag.call_args[0][0]
        assert "<@" not in question_arg


# --- on_message: error handling ---


@pytest.mark.asyncio
async def test_bot_sends_error_message_when_rag_fails(discord_bot):
    """When RAG_query raises an exception, the handler catches it
    and sends a fallback error message via message.channel."""
    on_message = discord_bot["handlers"]["on_message"]
    bot = discord_bot["bot"]

    other_user = MagicMock()
    message = _make_message(
        author=other_user,
        mentions=[bot.user],
        content=f"<@{bot.user.id}> question",
    )

    with patch("interfaces.discord_bot.RAG_query", side_effect=Exception("LLM error")):
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
