import pytest

from config import settings


@pytest.fixture
def use_ollama_for_testing():
    """Set the Ollama provider for tests that call the LLM."""
    original = settings.chat_provider_priority
    settings.chat_provider_priority = ["ollama_self_hosted"]
    yield
    settings.chat_provider_priority = original
