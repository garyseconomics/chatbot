import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from config import settings
from interfaces.discord_bot import (
    get_chat_memory,
    get_conversation_id,
    handle_message,
    process_message,
    send_greeting,
    should_respond,
    strip_bot_mention,
    wait_with_thinking,
)
from tests.discord_objects import (
    CHANNEL_ID,
    USER_ID,
    make_real_channel_message,
    make_real_dm_message,
)

# --- get_conversation_id ---
# With real discord.py objects (tests/discord_objects.py), so they break if the library changes.


def test_get_conversation_id_in_dm_is_the_user_id():
    message = make_real_dm_message()

    conversation_id = get_conversation_id(message)

    assert conversation_id == USER_ID


def test_get_conversation_id_in_channel_is_the_channel_id():
    message = make_real_channel_message()

    conversation_id = get_conversation_id(message)

    assert conversation_id == CHANNEL_ID


# --- get_chat_memory ---


def test_get_chat_memory_returns_the_same_memory_for_the_same_conversation(monkeypatch):
    """What is stored in a conversation's memory is still there on its next message."""
    # Start with no memories, so other tests don't affect this one
    monkeypatch.setattr("interfaces.discord_bot.chat_memories", {})
    first_memory = get_chat_memory(111)
    first_memory["conversation"].append("What is wealth?")

    second_memory = get_chat_memory(111)

    assert second_memory["conversation"] == ["What is wealth?"]


def test_get_chat_memory_keeps_conversations_separate(monkeypatch):
    """Each conversation id has its own memory."""
    monkeypatch.setattr("interfaces.discord_bot.chat_memories", {})
    get_chat_memory(111)["conversation"].append("What is wealth?")

    other_memory = get_chat_memory(222)

    assert other_memory == {"conversation": [], "knowledge": {}}


# --- Fake Discord objects ---

BOT_ID = 123


def _make_bot_user():
    bot_user = MagicMock()
    bot_user.id = BOT_ID
    return bot_user


def _make_message(
    text="What is wealth?", author_id=456, mentions=None, channel_name="youtube-chatbot"
):
    """A message in a server channel."""
    message = AsyncMock()
    message.content = text
    message.author.id = author_id
    message.mentions = mentions or []
    message.guild = MagicMock()
    message.channel = AsyncMock()
    message.channel.name = channel_name
    return message


def _make_dm_message(text="What is wealth?", author_id=456):
    message = _make_message(text, author_id)
    # Discord messages have no guild in DMs, and DM channels have no name
    message.guild = None
    message.channel.name = None
    return message


# --- should_respond ---


def test_ignores_own_messages():
    """The bot should not respond to its own messages to avoid infinite loops."""
    message = _make_message(author_id=BOT_ID)

    respond = should_respond(message, _make_bot_user(), is_dm=False)

    assert respond is False


def test_ignores_own_messages_in_dm(monkeypatch):
    monkeypatch.setattr(settings, "discord_dms_enabled", True)
    message = _make_dm_message(author_id=BOT_ID)

    respond = should_respond(message, _make_bot_user(), is_dm=True)

    assert respond is False


def test_ignores_guild_messages_without_mention(monkeypatch):
    """In guild channels, the bot only responds when explicitly @mentioned."""
    monkeypatch.setattr(settings, "discord_channel", "youtube-chatbot")
    message = _make_message(channel_name="youtube-chatbot")

    respond = should_respond(message, _make_bot_user(), is_dm=False)

    assert respond is False


def test_responds_when_mentioned_in_allowed_channel(monkeypatch):
    monkeypatch.setattr(settings, "discord_channel", "youtube-chatbot")
    bot_user = _make_bot_user()
    message = _make_message(mentions=[bot_user], channel_name="youtube-chatbot")

    respond = should_respond(message, bot_user, is_dm=False)

    assert respond is True


def test_ignores_mention_in_other_channel(monkeypatch):
    """The bot should ignore mentions in channels other than the allowed one."""
    monkeypatch.setattr(settings, "discord_channel", "youtube-chatbot")
    bot_user = _make_bot_user()
    message = _make_message(mentions=[bot_user], channel_name="general")

    respond = should_respond(message, bot_user, is_dm=False)

    assert respond is False


def test_responds_to_dm_without_mention(monkeypatch):
    """In DMs, the bot responds to any message without requiring an @mention."""
    monkeypatch.setattr(settings, "discord_dms_enabled", True)
    monkeypatch.setattr(settings, "testing_mode", False)
    message = _make_dm_message()

    respond = should_respond(message, _make_bot_user(), is_dm=True)

    assert respond is True


def test_responds_to_dm_with_mention(monkeypatch):
    monkeypatch.setattr(settings, "discord_dms_enabled", True)
    monkeypatch.setattr(settings, "testing_mode", False)
    bot_user = _make_bot_user()
    message = _make_dm_message()
    message.mentions = [bot_user]

    respond = should_respond(message, bot_user, is_dm=True)

    assert respond is True


# --- strip_bot_mention ---


def test_strips_mention_from_message():
    result = strip_bot_mention("<@123> What is GDP?", bot_id=123)
    assert result == "What is GDP?"


def test_strips_mention_at_end_of_message():
    result = strip_bot_mention("What is GDP? <@123>", bot_id=123)
    assert result == "What is GDP?"


def test_leaves_message_without_mention_unchanged():
    result = strip_bot_mention("What is GDP?", bot_id=123)
    assert result == "What is GDP?"


def test_strips_only_bot_mention_not_other_users():
    result = strip_bot_mention("<@123> ask <@456> about GDP", bot_id=123)
    assert result == "ask <@456> about GDP"


# --- wait_with_thinking ---

# @pytest.mark.asyncio tells pytest to run async test functions inside an event loop.
# Without it, pytest would get a coroutine object back and silently pass without
# running any of the test code.

# AsyncMock is a fake object where every method is async (can be awaited).
# When you access any attribute (like channel.send), it creates a new AsyncMock
# automatically — no need to define methods. It also records every call so you
# can check things like channel.send.assert_not_called().


@pytest.mark.asyncio
async def test_no_thinking_for_fast_task():
    """When the answer comes quickly, no thinking indicator should be sent."""
    channel = AsyncMock()

    async def fast():
        return "answer"

    task = asyncio.create_task(fast())
    await wait_with_thinking(channel, task, interval=0.05)

    channel.send.assert_not_called()
    channel.typing.assert_not_called()


@pytest.mark.asyncio
async def test_thinking_message_sent_for_slow_task():
    """When the answer takes longer than the interval, a visible 'Thinking...' message is sent."""
    channel = AsyncMock()

    async def slow():
        await asyncio.sleep(0.15)
        return "answer"

    task = asyncio.create_task(slow())
    await wait_with_thinking(channel, task, interval=0.05)

    channel.send.assert_called_with("🤔 Thinking...")


@pytest.mark.asyncio
async def test_typing_indicator_after_first_thinking_message():
    """After the first 'Thinking...' message, subsequent keepalives use
    trigger_typing instead of sending more messages."""
    channel = AsyncMock()

    async def very_slow():
        await asyncio.sleep(0.25)
        return "answer"

    task = asyncio.create_task(very_slow())
    await wait_with_thinking(channel, task, interval=0.05)

    # Only one "Thinking..." message was sent (not repeated)
    channel.send.assert_called_once_with("🤔 Thinking...")
    channel.typing.assert_called()


# --- send_greeting ---


@pytest.mark.asyncio
async def test_send_greeting_sends_to_matching_channel():
    settings.discord_channel = "test-channel"
    settings.bot_greeting = "Hello testers!"

    channel = AsyncMock()
    channel.name = "test-channel"

    await send_greeting([channel])

    channel.send.assert_called_once_with("Hello testers!")


@pytest.mark.asyncio
async def test_send_greeting_warns_when_channel_not_found(caplog):
    settings.discord_channel = "test-channel"

    channel = AsyncMock()
    channel.name = "other-channel"

    await send_greeting([channel])

    channel.send.assert_not_called()
    assert "WARNING" in caplog.text


@pytest.mark.asyncio
async def test_send_greeting_does_nothing_when_channels_are_off(monkeypatch, caplog):
    """An empty DISCORD_CHANNEL turns channels off: no greeting and no warning."""
    monkeypatch.setattr(settings, "discord_channel", "")

    channel = AsyncMock()
    channel.name = "youtube-chatbot"

    await send_greeting([channel])

    channel.send.assert_not_called()
    assert caplog.text == ""


# --- handle_message ---


def _fake_answer(monkeypatch, answer="A fake answer."):
    """Replace the orchestrator with a fake that always returns this answer."""
    mock_answer = AsyncMock(return_value=answer)
    monkeypatch.setattr("interfaces.discord_bot.answer_question", mock_answer)
    return mock_answer


@pytest.mark.asyncio
async def test_handle_message_sends_answer(monkeypatch):
    _fake_answer(monkeypatch, answer="Wealth is...")

    message = _make_message()
    await handle_message(message, _make_bot_user())

    sent_text = message.channel.send.call_args.args[0]
    assert "Wealth is..." in sent_text


@pytest.mark.asyncio
async def test_handle_message_long_answer_is_chunked(monkeypatch):
    answer = Path("./tests/test-data/long-answer.md").read_text()
    _fake_answer(monkeypatch, answer)

    message = _make_message()
    await handle_message(message, _make_bot_user())

    sent_text = ""
    for call in message.channel.send.call_args_list:
        sent_text += call.args[0]

    assert message.channel.send.call_count > 1
    assert answer in sent_text


@pytest.mark.asyncio
async def test_handle_message_sends_error_on_failure(monkeypatch):
    monkeypatch.setattr(
        "interfaces.discord_bot.answer_question", AsyncMock(side_effect=RuntimeError("boom"))
    )

    message = _make_message()
    await handle_message(message, _make_bot_user())

    message.channel.send.assert_called_once_with(settings.error_messages["DefaultError"])


# --- process_message ---


@pytest.mark.asyncio
async def test_bot_refuses_dms_when_dms_are_disabled(monkeypatch):
    # DISCORD_DMS_ENABLED not set in .env: DMs are off
    monkeypatch.setattr(settings, "discord_dms_enabled", None)
    monkeypatch.setattr(settings, "testing_mode", False)
    mock_answer = _fake_answer(monkeypatch)

    message = _make_dm_message()
    await process_message(message, _make_bot_user())

    # The user is told the bot doesn't answer DMs, and no answer is generated
    message.channel.send.assert_called_once_with(settings.discord_dms_off_message)
    mock_answer.assert_not_called()


@pytest.mark.asyncio
async def test_dm_gets_an_answer_when_dms_are_on(monkeypatch):
    monkeypatch.setattr(settings, "discord_dms_enabled", True)
    monkeypatch.setattr(settings, "testing_mode", False)
    _fake_answer(monkeypatch, answer="Wealth is...")

    message = _make_dm_message()
    await process_message(message, _make_bot_user())

    sent_text = message.channel.send.call_args.args[0]
    assert "Wealth is..." in sent_text


@pytest.mark.asyncio
async def test_dm_from_user_not_on_the_list_is_turned_away_in_testing_mode(monkeypatch):
    monkeypatch.setattr(settings, "discord_dms_enabled", True)
    monkeypatch.setattr(settings, "testing_mode", True)
    monkeypatch.setattr(settings, "discord_allowed_user_ids", [999])
    mock_answer = _fake_answer(monkeypatch)

    message = _make_dm_message(author_id=456)
    await process_message(message, _make_bot_user())

    message.channel.send.assert_called_once_with(settings.discord_dms_off_message)
    mock_answer.assert_not_called()


@pytest.mark.asyncio
async def test_dm_from_user_on_the_list_gets_an_answer_in_testing_mode(monkeypatch):
    monkeypatch.setattr(settings, "discord_dms_enabled", True)
    monkeypatch.setattr(settings, "testing_mode", True)
    monkeypatch.setattr(settings, "discord_allowed_user_ids", [456])
    _fake_answer(monkeypatch, answer="Wealth is...")

    message = _make_dm_message(author_id=456)
    await process_message(message, _make_bot_user())

    sent_text = message.channel.send.call_args.args[0]
    assert "Wealth is..." in sent_text


@pytest.mark.asyncio
async def test_bot_does_not_reply_to_its_own_dm_when_dms_are_off(monkeypatch):
    """Replying to its own "no DMs" message would make the bot reply to itself forever."""
    monkeypatch.setattr(settings, "discord_dms_enabled", False)
    monkeypatch.setattr(settings, "testing_mode", False)

    message = _make_dm_message(author_id=BOT_ID)
    await process_message(message, _make_bot_user())

    message.channel.send.assert_not_called()
