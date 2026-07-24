import langchain_core
import pytest
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_openai import OpenAIEmbeddings

from config import settings
from llm.llm_manager import LLM_Client

ollama_cloud_configured = bool(settings.providers["ollama_cloud"]["api_key"])
ollama_cloud_skip_reason = "OLLAMA_CLOUD_API_KEY not configured"


@pytest.mark.asyncio
async def test_chat_simple_prompt(use_ollama_for_testing):
    client = LLM_Client()
    response = await client.chat(prompt="Hello", user_id="Test")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)



@pytest.mark.asyncio
async def test_chat_with_prompt_template(use_ollama_for_testing):
    client = LLM_Client()
    prompt = ChatPromptTemplate.from_messages([("human", "Hello")])
    messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
    response = await client.chat(messages, user_id="Test")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


@pytest.mark.asyncio
async def test_chat_local_ollama():
    settings.chat_provider_priority = ["ollama_local"]
    client = LLM_Client()
    response = await client.chat(prompt="Hello", user_id="Test")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


@pytest.mark.asyncio
async def test_chat_self_hosted_ollama():
    settings.chat_provider_priority = ["ollama_self_hosted"]
    client = LLM_Client()
    response = await client.chat(prompt="Hello", user_id="Test")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


@pytest.mark.asyncio
@pytest.mark.skipif(not ollama_cloud_configured, reason=ollama_cloud_skip_reason)
async def test_chat_ollama_cloud():
    settings.chat_provider_priority = ["ollama_cloud"]
    client = LLM_Client()
    response = await client.chat(prompt="Hello", user_id="Test")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


@pytest.mark.asyncio
@pytest.mark.skip(reason="OPENROUTER_API_KEY in .env is invalid/expired (401 User not found) — needs manual key refresh, tracked separately")
async def test_chat_openrouter():
    settings.chat_provider_priority = ["openrouter"]
    client = LLM_Client()
    response = await client.chat(prompt="Hello. I'm trying OpenRouter.", user_id="Test")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


@pytest.mark.asyncio
async def test_chat_falls_back_on_invoke_error(monkeypatch):
    """When the first provider fails on ainvoke, chat() tries the next one."""
    # Add a bad provider: reachable server but nonexistent model → ainvoke will fail
    providers_with_bad = settings.providers
    providers_with_bad["bad_provider"] = {
        "type": "ollama",
        "url": settings.providers["ollama_self_hosted"]["url"],
        "api_key": None,
        "chat_model": "nonexistent_model_12345",
    }
    # Temporarily replace the providers @property so it returns our dict with bad_provider
    monkeypatch.setattr(type(settings), "providers", property(lambda self: providers_with_bad))
    settings.chat_provider_priority = ["bad_provider", "ollama_self_hosted"]

    client = LLM_Client()
    response = await client.chat(prompt="Hello", user_id="Test")

    assert isinstance(response, langchain_core.messages.ai.AIMessage)
    assert client.chat_provider_name == "ollama_self_hosted"


@pytest.mark.asyncio
async def test_provider_name_set_after_chat(use_ollama_for_testing):
    client = LLM_Client()
    assert client.chat_provider_name is None
    await client.chat(prompt="Hello", user_id="Test")
    assert client.chat_provider_name is not None


def test_get_embeddings_model(use_ollama_for_testing):
    client = LLM_Client()
    embeddings = client.get_embeddings_model()
    # Should return an embeddings object (we don't check the specific type
    # so vector_database_manager doesn't need to know about OllamaEmbeddings)
    assert hasattr(embeddings, "embed_query")


def test_get_embeddings_model_openrouter(use_openrouter_for_testing):
    client = LLM_Client()
    embeddings = client.get_embeddings_model()
    assert hasattr(embeddings, "embed_query")
    assert client.embeddings_provider_name == "openrouter"


def test_get_embeddings_model_returns_openai_embeddings_for_openai_type(monkeypatch):
    """get_embeddings_model() returns OpenAIEmbeddings when the provider type is 'openai'."""
    always_reachable = staticmethod(lambda host, timeout=3.0: True)
    monkeypatch.setattr(LLM_Client, "_is_host_reachable", always_reachable)
    monkeypatch.setattr(settings, "embeddings_provider_priority", ["openrouter"])
    client = LLM_Client()
    embeddings = client.get_embeddings_model()
    assert isinstance(embeddings, OpenAIEmbeddings)


def test_get_embeddings_model_is_cached(monkeypatch):
    """Second call to get_embeddings_model() returns the same object without re-selecting a provider."""
    always_reachable = staticmethod(lambda host, timeout=3.0: True)
    monkeypatch.setattr(LLM_Client, "_is_host_reachable", always_reachable)
    monkeypatch.setattr(settings, "embeddings_provider_priority", ["openrouter"])
    client = LLM_Client()
    first = client.get_embeddings_model()
    second = client.get_embeddings_model()
    assert first is second


@pytest.mark.asyncio
async def test_chat_raises_when_all_providers_unreachable(monkeypatch):
    """ConnectionError is raised after max_attempts when no provider is reachable."""
    # Make all hosts unreachable so every provider fails on availability
    always_unreachable = staticmethod(lambda host, timeout=3.0: False)
    monkeypatch.setattr(LLM_Client, "_is_host_reachable", always_unreachable)
    settings.chat_provider_priority = ["ollama_local"]

    client = LLM_Client()

    with pytest.raises(ConnectionError) as exc_info:
        await client.chat(prompt="Hello", user_id="Test")

    error_message = str(exc_info.value)
    assert "ollama_local" in error_message
    assert client.providers_errors["ollama_local"] == "Host unreachable"
    assert "Host unreachable" in error_message


@pytest.mark.asyncio
async def test_chat_raises_when_invoke_always_fails(monkeypatch):
    """ConnectionError is raised when providers are reachable but ainvoke always fails."""
    # Use a reachable server but with a nonexistent model — ainvoke will return a 500 error
    providers_all_bad = {
        "bad_provider": {
            "type": "ollama",
            "url": settings.providers["ollama_self_hosted"]["url"],
            "api_key": None,
            "chat_model": "nonexistent_model_12345",
        },
    }
    monkeypatch.setattr(type(settings), "providers", property(lambda self: providers_all_bad))
    settings.chat_provider_priority = ["bad_provider"]

    client = LLM_Client()

    with pytest.raises(ConnectionError) as exc_info:
        await client.chat(prompt="Hello", user_id="Test")

    error_message = str(exc_info.value)
    assert "bad_provider" in error_message
    assert "nonexistent_model_12345" in client.providers_errors["bad_provider"]
    assert "nonexistent_model_12345" in error_message


@pytest.mark.asyncio
async def test_chat_reports_errors_from_all_providers(monkeypatch):
    """ConnectionError includes the right error for each provider that failed."""
    providers_mixed = {
        # Port 1 — connection refused, fast failure
        "unreachable_provider": {
            "type": "ollama",
            "url": "http://localhost:1",
            "api_key": None,
            "chat_model": "any_model",
        },
        # Reachable server but nonexistent model — ainvoke will fail
        "bad_model_provider": {
            "type": "ollama",
            "url": settings.providers["ollama_self_hosted"]["url"],
            "api_key": None,
            "chat_model": "nonexistent_model_12345",
        },
    }
    monkeypatch.setattr(type(settings), "providers", property(lambda self: providers_mixed))
    settings.chat_provider_priority = ["unreachable_provider", "bad_model_provider"]

    client = LLM_Client()

    # pytest.raises(...) as exc_info captures the exception so we can inspect its message
    with pytest.raises(ConnectionError) as exc_info:
        await client.chat(prompt="Hello", user_id="Test")

    error_message = str(exc_info.value)
    assert "unreachable_provider" in error_message
    assert "bad_model_provider" in error_message
    # Verify each provider got the right type of error
    assert client.providers_errors["unreachable_provider"] == "Host unreachable"
    expected_model_error = "model 'nonexistent_model_12345' not found (status code: 404)"
    assert "nonexistent_model_12345" in client.providers_errors["bad_model_provider"]
    assert "nonexistent_model_12345" in error_message

    # TODO: might need more robust error checking now we have OpenAI client in workflow


def test_get_chat_model_returns_ollama_for_ollama_type(monkeypatch):
    """If the provider type is 'ollama', get_chat_model() returns a ChatOllama instance."""
    always_reachable = staticmethod(lambda host, timeout=3.0: True)
    monkeypatch.setattr(LLM_Client, "_is_host_reachable", always_reachable)
    settings.chat_provider_priority = ["ollama_local"]
    client = LLM_Client()
    model = client.get_chat_model()
    assert isinstance(model, ChatOllama)

# {"detail":{"error":{"message":"The model 'ollama/nonexistent_model_12345' does not exist.","type":"invalid_request_error","param":"model","code":"model_not_found"}}} (status code: 404)
