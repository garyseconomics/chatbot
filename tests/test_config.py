from config import Settings


def test_constructor_overrides_values():
    s = Settings(
        ollama_host_remote="http://remote:11434",
        remote_llm="llama3:70b",
        chunk_size=2048,
        show_logs=False,
    )
    assert s.ollama_host_remote == "http://remote:11434"
    assert s.remote_llm == "llama3:70b"
    assert s.chunk_size == 2048
    assert s.show_logs is False


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
    s = Settings(chunk_size="512", show_logs="false", batch_size="20")
    assert s.chunk_size == 512
    assert s.show_logs is False
    assert s.batch_size == 20
