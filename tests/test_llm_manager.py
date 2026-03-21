import langchain_core
import pytest
from langchain_core.prompts import ChatPromptTemplate

from config import settings
from llm.llm_manager import LLM_Client


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
async def test_chat_ollama_cloud():
    settings.chat_provider_priority = ["ollama_cloud"]
    client = LLM_Client()
    response = await client.chat(prompt="Hello", user_id="Test")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


@pytest.mark.asyncio
async def test_chat_falls_back_on_invoke_error(monkeypatch):
    """When the first provider fails on ainvoke, chat() tries the next one."""
    # Add a bad provider: reachable server but nonexistent model → ainvoke will fail
    providers_with_bad = settings.providers
    providers_with_bad["bad_provider"] = {
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
    assert client.provider_name == "ollama_self_hosted"


@pytest.mark.asyncio
async def test_provider_name_set_after_chat(use_ollama_for_testing):
    client = LLM_Client()
    assert client.provider_name is None
    await client.chat(prompt="Hello", user_id="Test")
    assert client.provider_name is not None


@pytest.mark.asyncio
async def test_chat_model_returns_model_name(use_ollama_for_testing):
    client = LLM_Client()
    assert client.chat_model is None
    await client.chat(prompt="Hello", user_id="Test")
    expected_model = settings.providers[client.provider_name]["chat_model"]
    assert client.chat_model == expected_model


def test_get_embedding_model(use_ollama_for_testing):
    client = LLM_Client()
    embeddings = client.get_embedding_model()
    # Should return an embeddings object (we don't check the specific type
    # so vector_database_manager doesn't need to know about OllamaEmbeddings)
    assert hasattr(embeddings, "embed_query")


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
    expected_model_error = "model 'nonexistent_model_12345' not found (status code: 404)"
    assert client.providers_errors["bad_provider"] == expected_model_error
    assert expected_model_error in error_message


@pytest.mark.asyncio
async def test_chat_reports_errors_from_all_providers(monkeypatch):
    """ConnectionError includes the right error for each provider that failed."""
    providers_mixed = {
        # Port 1 — connection refused, fast failure
        "unreachable_provider": {
            "url": "http://localhost:1",
            "api_key": None,
            "chat_model": "any_model",
        },
        # Reachable server but nonexistent model — ainvoke will fail
        "bad_model_provider": {
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
    assert client.providers_errors["bad_model_provider"] == expected_model_error
    assert expected_model_error in error_message
