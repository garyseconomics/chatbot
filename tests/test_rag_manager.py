import pytest

from config import settings
from rag.rag_manager import RAG_query, build_error_state

ollama_cloud_configured = bool(settings.ollama_cloud_api_key and settings.ollama_cloud_url)
skip_ollama_cloud = "Ollama Cloud not configured (OLLAMA_CLOUD_API_KEY, OLLAMA_CLOUD_URL)"

# --- build_error_state() tests ---


def test_build_error_state_known_error():
    """When the exception type is in settings.error_messages, use that message."""
    result = build_error_state(ConnectionError("refused"), "q", "user1")

    assert result["answer"] == settings.error_messages["ConnectionError"]
    assert result["context"] == []
    assert result["question"] == "q"
    assert result["user_id"] == "user1"


def test_build_error_state_unknown_error():
    """When the exception type is NOT in settings.error_messages, use the default."""
    result = build_error_state(RuntimeError("something"), "q", "user1")

    assert result["answer"] == settings.error_messages["DefaultError"]
    assert result["context"] == []


# --- End-to-end test (hits real Ollama and vector DB) ---


@pytest.mark.ollama_cloud
@pytest.mark.skipif(not ollama_cloud_configured, reason=skip_ollama_cloud)
@pytest.mark.asyncio
async def test_rag_query_end_to_end(use_ollama_for_testing):
    question = "What is wealth?"
    response = await RAG_query(question, user_id="test")

    assert isinstance(response["answer"], str)
    assert len(response["answer"]) > 0


@pytest.mark.ollama_cloud
@pytest.mark.skipif(not ollama_cloud_configured, reason=skip_ollama_cloud)
@pytest.mark.asyncio
async def test_rag_query_ollama_cloud():
    """Verify ollama_cloud chat model returns a non-empty answer."""
    settings.chat_provider_priority = ["ollama_cloud"]
    question = "What is wealth?"
    response = await RAG_query(question, user_id="test")
    assert isinstance(response["answer"], str)
    assert len(response["answer"]) > 0
