import asyncio
from unittest.mock import AsyncMock

import pytest

from interfaces.discord_bot import should_respond, strip_bot_mention, wait_with_thinking


# --- should_respond ---


def test_ignores_own_messages():
    """The bot should not respond to its own messages to avoid infinite loops."""
    respond = should_respond(author_id=123, bot_id=123, is_dm=False, is_mentioned=False)
    assert respond is False


def test_ignores_own_messages_in_dm():
    respond = should_respond(author_id=123, bot_id=123, is_dm=True, is_mentioned=False)
    assert respond is False


def test_ignores_guild_messages_without_mention():
    """In guild channels, the bot only responds when explicitly @mentioned."""
    respond = should_respond(author_id=999, bot_id=123, is_dm=False, is_mentioned=False)
    assert respond is False


def test_responds_when_mentioned_in_guild():
    respond = should_respond(author_id=999, bot_id=123, is_dm=False, is_mentioned=True)
    assert respond is True


def test_responds_to_dm_without_mention():
    """In DMs, the bot responds to any message without requiring an @mention."""
    respond = should_respond(author_id=999, bot_id=123, is_dm=True, is_mentioned=False)
    assert respond is True


def test_responds_to_dm_with_mention():
    respond = should_respond(author_id=999, bot_id=123, is_dm=True, is_mentioned=True)
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
    """When RAG responds quickly, no thinking indicator should be sent."""
    channel = AsyncMock()

    async def fast():
        return "answer"

    task = asyncio.create_task(fast())
    await wait_with_thinking(channel, task, interval=0.05)

    channel.send.assert_not_called()
    channel.trigger_typing.assert_not_called()


@pytest.mark.asyncio
async def test_thinking_message_sent_for_slow_task():
    """When RAG takes longer than the interval, a visible 'Thinking...' message is sent."""
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
    channel.trigger_typing.assert_called()