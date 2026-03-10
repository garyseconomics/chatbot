from config import Settings, settings


def test_constructor_overrides_values():
    s = Settings(
        ollama_host_remote="http://remote:11434",
        remote_llm="llama3:70b",
        chunk_size=2048,
        log_level="WARNING",
    )
    assert s.ollama_host_remote == "http://remote:11434"
    assert s.remote_llm == "llama3:70b"
    assert s.chunk_size == 2048
    assert s.log_level == "WARNING"


def test_secrets_default_to_empty():
    """Bot tokens and API keys default to empty when not in env."""
    s = Settings(
        _env_file=None,
        telegram_token="",
        discord_token="",
        langfuse_public_key="",
        langfuse_secret_key="",
    )
    assert s.telegram_token == ""
    assert s.discord_token == ""
    assert s.langfuse_public_key == ""
    assert s.langfuse_secret_key == ""


def test_type_coercion():
    """Pydantic coerces string values to the declared field types."""
    s = Settings(chunk_size="512", log_level="info", batch_size="20")
    assert s.chunk_size == 512
    assert s.log_level == "info"
    assert s.batch_size == 20


def test_ollama_hosts_are_configured():
    """Both Ollama hosts must be configured. Without them the chatbot can't reach any LLM."""
    assert settings.ollama_host_local, (
        "OLLAMA_HOST_LOCAL is not configured. "
        "Set it in .env (e.g. OLLAMA_HOST_LOCAL=http://localhost:11434)"
    )
    assert settings.ollama_host_remote, (
        "OLLAMA_HOST_REMOTE is not configured. "
        "Set it in .env (e.g. OLLAMA_HOST_REMOTE=http://your-server:11434)"
    )
