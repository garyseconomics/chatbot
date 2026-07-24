import pytest

from config import settings


@pytest.fixture
def use_ollama_for_testing():
    """Set the Ollama provider for tests that call the LLM.
    Using a small model in the self hosted provider is the fastest option."""
    original = settings.chat_provider_priority
    settings.chat_provider_priority = ["ollama_local"]
    settings.providers["ollama_local"]["chat_model"] = "qwen3:4b"
    yield
    settings.chat_provider_priority = original

@pytest.fixture
def use_openrouter_for_testing():
    """Set the OpenRouter provider for tests that call the LLM."""
    original_chat = settings.chat_provider_priority
    original_embeddings = settings.embeddings_provider_priority
    original_embeddings_model = settings.embeddings_model
    settings.chat_provider_priority = ["openrouter"]
    settings.embeddings_provider_priority = ["openrouter"]
    settings.embeddings_model = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
    yield
    settings.chat_provider_priority = original_chat
    settings.embeddings_provider_priority = original_embeddings
    settings.embeddings_model = original_embeddings_model
