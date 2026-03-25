import pytest

from config import settings


@pytest.fixture
def use_ollama_for_testing():
    """Set the Ollama provider for tests that call the LLM.
    Using a small model in the self hosted provider is the fastest option."""
    original = settings.chat_provider_priority
    settings.chat_provider_priority = ["ollama_self_hosted"]
    settings.providers["ollama_self_hosted"]["chat_model"] = "qwen3:4b"
    yield
    settings.chat_provider_priority = original
