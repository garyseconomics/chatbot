from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from langchain_core.documents import Document

# The Telegram bot has two async handler functions:
# - start(update, context): sends the greeting when a user sends /start
# - question(update, context): receives a text message, calls RAG_query,
#   appends video links if any, and sends the answer back
#
# Both handlers receive a Telegram Update (contains the message and chat info)
# and a context (provides access to the bot for sending replies).
# We mock these objects and the RAG pipeline to test the handlers in isolation.


def _make_update(text: str = "What is inflation?", chat_id: int = 42) -> MagicMock:
    """Create a mock Telegram Update with the given message text and chat id."""
    update = MagicMock()
    update.message.text = text
    update.effective_chat.id = chat_id
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
    """The /start handler sends the configured greeting to the user's chat."""
    update = _make_update(chat_id=99)
    context = _make_context()

    with patch("interfaces.telegram_bot.settings") as mock_settings:
        mock_settings.bot_greeting = "Welcome!"
        from interfaces.telegram_bot import start

        await start(update, context)

    context.bot.send_message.assert_called_once_with(chat_id=99, text="Welcome!")


# --- question handler ---


@pytest.mark.asyncio
async def test_question_calls_rag_with_user_message():
    """The question handler passes the user's message text to RAG_query."""
    update = _make_update(text="How does GDP work?")
    context = _make_context()

    with patch(
        "interfaces.telegram_bot.RAG_query",
        return_value={"answer": "Answer", "context": [], "question": "How does GDP work?"},
    ) as mock_rag:
        from interfaces.telegram_bot import question

        await question(update, context)

    mock_rag.assert_called_once_with("How does GDP work?")


@pytest.mark.asyncio
async def test_question_sends_answer_to_chat():
    """The question handler sends the RAG answer back to the user's chat."""
    update = _make_update(chat_id=7)
    context = _make_context()

    with patch(
        "interfaces.telegram_bot.RAG_query",
        return_value={"answer": "Inflation is rising prices.", "context": [], "question": "q"},
    ):
        from interfaces.telegram_bot import question

        await question(update, context)

    # Verify the answer was sent to the correct chat
    context.bot.send_message.assert_called_once()
    call_kwargs = context.bot.send_message.call_args
    assert call_kwargs.kwargs["chat_id"] == 7
    assert "Inflation is rising prices." in call_kwargs.kwargs["text"]


@pytest.mark.asyncio
async def test_question_appends_video_links_when_context_has_documents():
    """When RAG returns context documents, the answer includes video links."""
    update = _make_update()
    context = _make_context()

    # Provide a context document with a source filename — the bot extracts the
    # video ID from it and appends the YouTube link to the answer
    with patch(
        "interfaces.telegram_bot.RAG_query",
        return_value={
            "answer": "GDP measures output.",
            "context": [
                Document(page_content="...", metadata={"source": "abc123_en.srt"}),
            ],
            "question": "q",
        },
    ):
        from interfaces.telegram_bot import question

        await question(update, context)

    sent_text = context.bot.send_message.call_args.kwargs["text"]
    assert "GDP measures output." in sent_text
    assert "youtube.com" in sent_text


@pytest.mark.asyncio
async def test_question_no_video_links_when_context_is_empty():
    """When RAG returns no context, the answer is sent without video links."""
    update = _make_update()
    context = _make_context()

    with patch(
        "interfaces.telegram_bot.RAG_query",
        return_value={"answer": "No info.", "context": [], "question": "q"},
    ):
        from interfaces.telegram_bot import question

        await question(update, context)

    # Only the plain answer — no video links appended
    sent_text = context.bot.send_message.call_args.kwargs["text"]
    assert sent_text == "No info."
