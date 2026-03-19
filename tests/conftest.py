import pytest

from config import settings


@pytest.fixture(autouse=True)
def use_local_ollama():
    """Force all tests to use local Ollama by default."""
    original = settings.chat_provider_priority
    settings.chat_provider_priority = ["ollama_local"]
    yield
    settings.chat_provider_priority = original
