import asyncio

import pytest
from langfuse import Langfuse

from config import settings
from rag.langfuse_helpers import create_langfuse_client

langfuse_configured = all(
    [
        settings.langfuse_public_key,
        settings.langfuse_secret_key,
    ]
)

skip_reason = "Langfuse env vars not configured (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)"


@pytest.mark.langfuse
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
def test_langfuse_client_connects(use_ollama_for_testing):
    langfuse_client = create_langfuse_client()
    assert isinstance(langfuse_client, Langfuse)
    assert langfuse_client.auth_check()


@pytest.mark.langfuse
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
@pytest.mark.asyncio
async def test_rag_query_sends_trace_with_all_metadata(use_ollama_for_testing):
    """Verify that RAG_query sends a single trace with user_id, chat and embedding metadata."""
    from rag.rag_manager import RAG_query

    test_user_id = "test_rag_trace"
    await RAG_query(question="What is inflation?", user_id=test_user_id)

    # Wait for Langfuse to index the trace
    langfuse_client = create_langfuse_client()
    langfuse_client.flush()
    await asyncio.sleep(2)

    # Fetch traces filtered by user_id to find the one we just created
    response = langfuse_client.api.trace.list(user_id=test_user_id)
    assert len(response.data) > 0, "No trace found for test user"
    latest_trace = response.data[0]

    assert latest_trace.user_id == test_user_id
    assert latest_trace.name == settings.app_name
    # Check that both chat and embedding metadata are present
    tests_provider = "ollama_self_hosted"
    chat_model = settings.providers[tests_provider]["chat_model"]
    assert latest_trace.metadata["chat_model"] == chat_model
    assert latest_trace.metadata["chat_provider"] == tests_provider
    assert latest_trace.metadata["embedding_model"] == settings.embeddings_model
    assert latest_trace.metadata["embedding_provider"] == tests_provider
