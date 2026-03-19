from unittest.mock import AsyncMock, MagicMock

import pytest

from config import settings
from interfaces.telegram_bot import question, start


def _make_update(text="What is inflation?", chat_id=42, user_id=100) -> MagicMock:
    """Create a mock Telegram Update with the given message text and chat id."""
    update = MagicMock()
    update.message.text = text
    update.effective_chat.id = chat_id
    update.effective_user.id = user_id
    return update


def _make_context() -> MagicMock:
    """Create a mock Telegram context with an async send_message."""
    context = MagicMock()
    # send_message is a coroutine in the real bot, so we use AsyncMock
    context.bot.send_message = AsyncMock()
    return context


# --- /start command ---


@pytest.mark.asyncio
async def test_start_sends_greeting():
    """The /start handler runs without errors."""
    update = _make_update()
    context = _make_context()

    await start(update, context)

    sent_text = context.bot.send_message.call_args.kwargs["text"]
    assert sent_text == settings.bot_greeting


# --- question handler ---


@pytest.mark.asyncio
async def test_question_runs_without_errors(monkeypatch):
    """The question handler runs end-to-end without crashing."""
    mock_rag = AsyncMock(return_value={
        "answer": "Wealth is...",
        "context": [],
        "question": "What is wealth?",
    })
    monkeypatch.setattr("interfaces.telegram_bot.RAG_query", mock_rag)

    update = _make_update(text="What is wealth?")
    context = _make_context()

    await question(update, context)

    sent_text = context.bot.send_message.call_args.kwargs["text"]
    assert "Wealth is..." in sent_text