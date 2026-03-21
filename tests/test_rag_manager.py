import pytest

from config import settings
from rag.rag_manager import RAG_query, build_error_state

# --- build_error_state() tests ---


def test_build_error_state_known_error():
    """When the exception type is in settings.error_messages, use that message."""
    result = build_error_state(ConnectionError("refused"), "q", "user1")

    assert result["answer"] == settings.error_messages["ConnectionError"]
    assert result["context"] == []
    assert result["question"] == "q"
    assert result["user_id"] == "user1"
    assert result["chat_model"] == ""


def test_build_error_state_unknown_error():
    """When the exception type is NOT in settings.error_messages, use the default."""
    result = build_error_state(RuntimeError("something"), "q", "user1")

    assert result["answer"] == settings.error_messages["DefaultError"]
    assert result["context"] == []


# --- End-to-end test (hits real Ollama and vector DB) ---


@pytest.mark.asyncio
async def test_rag_query_end_to_end(use_ollama_for_testing):
    question = "What is wealth?"
    response = await RAG_query(question, user_id="test")

    assert isinstance(response["answer"], str)
    assert isinstance(response["chat_model"], str)
    assert len(response["chat_model"]) > 0
