from pathlib import Path
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
    # A real dict, like the one python-telegram-bot keeps for each chat
    context.chat_data = {}
    return context


# --- /start command ---


@pytest.mark.asyncio
async def test_start_sends_greeting(monkeypatch):
    """The /start handler runs without errors."""
    monkeypatch.setattr(settings, "testing_mode", False)
    update = _make_update()
    context = _make_context()

    await start(update, context)

    sent_text = context.bot.send_message.call_args.kwargs["text"]
    assert sent_text == settings.bot_greeting


# --- question handler ---


@pytest.mark.asyncio
async def test_question_runs_without_errors(monkeypatch):
    """The question handler runs end-to-end without crashing."""
    monkeypatch.setattr(settings, "testing_mode", False)
    mock_answer = AsyncMock(return_value="Wealth is...")
    monkeypatch.setattr("interfaces.telegram_bot.answer_question", mock_answer)

    update = _make_update(text="What is wealth?")
    context = _make_context()

    await question(update, context)

    sent_text = context.bot.send_message.call_args.kwargs["text"]
    assert "Wealth is..." in sent_text

@pytest.mark.asyncio
async def test_question_runs_without_errors_answer_longer_than_max_limit(monkeypatch):
    """The question handler runs end-to-end without crashing."""
    monkeypatch.setattr(settings, "testing_mode", False)

    answer = Path("./tests/test-data/long-answer.md").read_text()
    mock_answer = AsyncMock(return_value=answer)
    monkeypatch.setattr("interfaces.telegram_bot.answer_question", mock_answer)

    update = _make_update(text="What is wealth?")
    context = _make_context()

    await question(update, context)

    sent_text = ""
    for call in context.bot.send_message.await_args_list:
        sent_text = sent_text + call[1]["text"]

    assert len(context.bot.send_message.await_args_list) == 2
    assert answer in sent_text

@pytest.mark.asyncio
async def test_question_sends_error_message_on_failure(monkeypatch):
    """When an unexpected error occurs, the bot sends the default error message."""
    monkeypatch.setattr(settings, "testing_mode", False)
    mock_answer = AsyncMock(side_effect=RuntimeError("something broke"))
    monkeypatch.setattr("interfaces.telegram_bot.answer_question", mock_answer)

    update = _make_update(text="What is wealth?")
    context = _make_context()

    await question(update, context)

    sent_text = context.bot.send_message.call_args.kwargs["text"]
    assert sent_text == settings.error_messages["DefaultError"]


# --- testing mode ---


@pytest.mark.asyncio
async def test_question_turns_away_users_not_on_the_list_in_testing_mode(monkeypatch):
    """In testing mode, a user who isn't on the list gets the "not open" message, not an answer."""
    monkeypatch.setattr(settings, "testing_mode", True)
    monkeypatch.setattr(settings, "telegram_allowed_user_ids", [])
    mock_answer = AsyncMock(return_value="Wealth is...")
    monkeypatch.setattr("interfaces.telegram_bot.answer_question", mock_answer)

    update = _make_update(text="What is wealth?", user_id=100)
    context = _make_context()

    await question(update, context)

    sent_text = context.bot.send_message.call_args.kwargs["text"]
    assert sent_text == settings.bot_not_open_message
    mock_answer.assert_not_called()


@pytest.mark.asyncio
async def test_question_answers_users_on_the_list_in_testing_mode(monkeypatch):
    """In testing mode, a user who is on the list gets an answer."""
    monkeypatch.setattr(settings, "testing_mode", True)
    monkeypatch.setattr(settings, "telegram_allowed_user_ids", [100])
    mock_answer = AsyncMock(return_value="Wealth is...")
    monkeypatch.setattr("interfaces.telegram_bot.answer_question", mock_answer)

    update = _make_update(text="What is wealth?", user_id=100)
    context = _make_context()

    await question(update, context)

    sent_text = context.bot.send_message.call_args.kwargs["text"]
    assert "Wealth is..." in sent_text
