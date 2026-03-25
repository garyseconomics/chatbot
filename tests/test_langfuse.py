import pytest
from langfuse import Langfuse

from config import settings
from llm.llm_manager import LLM_Client

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
    llm_client = LLM_Client()
    langfuse_client = llm_client.langfuse_client
    assert isinstance(langfuse_client, Langfuse)
    assert langfuse_client.auth_check()


@pytest.mark.langfuse
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
@pytest.mark.asyncio
async def test_chat_sends_trace_to_langfuse_real(use_ollama_for_testing):
    """Verify that chat() sends user_id, model and provider to Langfuse (real API)."""
    llm_client = LLM_Client()
    test_user_id = "test_trace_user_real"
    await llm_client.chat(prompt="Hello", user_id=test_user_id)

    # Fetch traces filtered by user_id to find the one we just created
    response = llm_client.langfuse_client.api.trace.list(user_id=test_user_id)
    assert len(response.data) > 0, "No trace found for test user"
    latest_trace = response.data[0]

    assert latest_trace.user_id == test_user_id
    assert latest_trace.metadata["model"] == llm_client.chat_model.model
    assert latest_trace.metadata["provider"] == llm_client.chat_provider_name
