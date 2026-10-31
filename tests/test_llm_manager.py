import langchain_core
import pytest
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from config import settings
from llm.llm_manager import LLM_Client

# The use_test_provider fixture in conftest.py makes every test use only this provider,
# unless the test sets its own priority.
TEST_PROVIDER = settings.test_chat_provider


def provider_with_bad_model() -> dict:
    """The test provider's settings with a nonexistent model: reachable, but ainvoke will fail."""
    provider = settings.providers[TEST_PROVIDER].copy()
    provider["chat_model"] = "nonexistent_model_12345"
    return provider


@pytest.mark.asyncio
async def test_chat_simple_prompt():
    client = LLM_Client()
    response = await client.chat(prompt="Hello", user_id="Test")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


@pytest.mark.asyncio
async def test_chat_with_prompt_template():
    client = LLM_Client()
    prompt = ChatPromptTemplate.from_messages([("human", "Hello")])
    messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
    response = await client.chat(messages, user_id="Test")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


@pytest.mark.asyncio
async def test_chat_falls_back_on_invoke_error(monkeypatch):
    """When the first provider fails on ainvoke, chat() tries the next one."""
    # Add a bad provider: reachable server but nonexistent model → ainvoke will fail
    providers_with_bad = settings.providers
    providers_with_bad["bad_provider"] = provider_with_bad_model()
    # Temporarily replace the providers @property so it returns our dict with bad_provider
    monkeypatch.setattr(type(settings), "providers", property(lambda self: providers_with_bad))
    settings.chat_provider_priority = ["bad_provider", TEST_PROVIDER]

    client = LLM_Client()
    response = await client.chat(prompt="Hello", user_id="Test")

    assert isinstance(response, langchain_core.messages.ai.AIMessage)
    assert client.chat_provider_name == TEST_PROVIDER


@pytest.mark.asyncio
async def test_provider_name_set_after_chat():
    client = LLM_Client()
    assert client.chat_provider_name is None
    await client.chat(prompt="Hello", user_id="Test")
    assert client.chat_provider_name is not None


@pytest.mark.asyncio
async def test_chat_raises_when_all_providers_unreachable(monkeypatch):
    """ConnectionError is raised after max_attempts when no provider is reachable."""
    # Make all hosts unreachable so every provider fails on availability
    always_unreachable = staticmethod(lambda host, timeout=3.0: False)
    monkeypatch.setattr(LLM_Client, "_is_host_reachable", always_unreachable)

    client = LLM_Client()

    with pytest.raises(ConnectionError) as exc_info:
        await client.chat(prompt="Hello", user_id="Test")

    error_message = str(exc_info.value)
    assert TEST_PROVIDER in error_message
    assert client.providers_errors[TEST_PROVIDER] == "Host unreachable"
    assert "Host unreachable" in error_message


@pytest.mark.asyncio
async def test_chat_raises_when_invoke_always_fails(monkeypatch):
    """ConnectionError is raised when providers are reachable but ainvoke always fails."""
    # Use a reachable server but with a nonexistent model — ainvoke will return an error
    providers_all_bad = {"bad_provider": provider_with_bad_model()}
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
        "bad_model_provider": provider_with_bad_model(),
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
    # A provider defined here, so the test doesn't depend on which providers are configured
    ollama_provider = {
        "ollama_provider": {
            "type": "ollama",
            "url": "http://localhost:1",
            "api_key": None,
            "chat_model": "any_model",
        },
    }
    monkeypatch.setattr(type(settings), "providers", property(lambda self: ollama_provider))
    settings.chat_provider_priority = ["ollama_provider"]
    client = LLM_Client()
    model = client.get_chat_model()
    assert isinstance(model, ChatOllama)

# {"detail":{"error":{"message":"The model 'ollama/nonexistent_model_12345' does not exist.","type":"invalid_request_error","param":"model","code":"model_not_found"}}} (status code: 404)
