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

def test_ollama_hosts_are_configured():
    """Local Ollama host must be configured. Self-hosted is optional."""
    assert settings.ollama_local_host, (
        "OLLAMA_LOCAL_HOST is not configured. "
        "Set it in .env (e.g. OLLAMA_LOCAL_HOST=http://localhost:11434)"
    )