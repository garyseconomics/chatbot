from config import settings


def test_basic_configuration():
    assert isinstance(settings.app_name, str)
    assert isinstance(settings.log_level, str)
    assert isinstance(settings.bot_greeting, str)

def test_vectorized_database_configuration():
    assert isinstance(settings.database_path, str)
    assert isinstance(settings.collection_name, str)
    assert isinstance(settings.chunk_size, int)
    assert isinstance(settings.chunk_overlap, int)
    assert isinstance(settings.batch_size, int)

def test_local_ollama_host_is_configured():
    """Local Ollama host must be configured."""
    assert settings.ollama_local_host_url, (
        "OLLAMA_LOCAL_HOST is not configured. "
        "Set it in .env (e.g. OLLAMA_LOCAL_HOST=http://localhost:11434)"
    )
    local = settings.providers["ollama_local"]
    assert isinstance(local["url"], str)
    assert local["url"] == settings.ollama_local_host_url

def test_remote_llm_providers_config():
    self_hosted = settings.providers["ollama_self_hosted"]
    assert isinstance(self_hosted["url"], str)
    assert isinstance(self_hosted["chat_model"], str)
    ollama_cloud = settings.providers["ollama_cloud"]
    assert isinstance(ollama_cloud["url"], str)
    assert isinstance(ollama_cloud["chat_model"], str)

def test_chat_providers_priority_config():
    assert len(settings.chat_provider_priority) > 1
    assert isinstance(settings.chat_provider_priority[0], str)
    for provider_name in settings.chat_provider_priority:
        assert provider_name in settings.providers
