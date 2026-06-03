import pytest

from config import settings


@pytest.fixture
def use_ollama_for_testing():
    """Set the Ollama provider for tests that call the LLM.
    Using a small model in the self hosted provider is the fastest option."""
    original = settings.chat_provider_priority
    settings.chat_provider_priority = ["ollama_cloud"]
    settings.providers["ollama_cloud"]["chat_model"] = "qwen3:4b"
    yield
    settings.chat_provider_priority = original

@pytest.fixture
def use_openrouter_for_testing():
    """Set the OpenRouter provider for tests that call the LLM."""
    original = settings.chat_provider_priority
    settings.chat_provider_priority = ["openrouter"]
    # Uncommenting this will also make the test use OpenRouter for embeddings.
    #settings.embeddings_provider_priority = ["openrouter"]
    # This will change the model used for embeddings.
    #settings.embeddings_model = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
    yield
    settings.chat_provider_priority = original
