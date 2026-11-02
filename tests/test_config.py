import os

from config import (
    DEFAULT_CHAT_PROVIDER_PRIORITY,
    Settings,
    build_providers,
    load_providers_config,
    settings,
    turn_tracing_off_by_default,
)


def test_basic_configuration():
    assert isinstance(settings.app_name, str)
    assert isinstance(settings.log_level, str)
    assert isinstance(settings.bot_greeting, str)


def test_test_chat_provider_is_configured():
    """The provider used by the tests must be defined in providers.json."""
    assert settings.test_chat_provider in settings.providers, (
        f"TEST_CHAT_PROVIDER is {settings.test_chat_provider!r}, which is not in providers.json"
    )


def test_chat_providers_priority_config():
    # A new Settings(), because the use_test_provider fixture replaces the priority in
    # `settings` during the tests. Storing the list keeps failure messages from printing
    # the whole settings object, which includes secrets.
    priority = Settings().chat_provider_priority
    # One provider is enough; more give the chatbot a fallback.
    assert len(priority) >= 1
    assert isinstance(priority[0], str)
    for provider_name in priority:
        assert provider_name in settings.providers


# The providers' settings are read from providers.json, and their API keys from .env.
# The priority lists are read from .env.


def test_sample_file_defines_the_default_chat_providers():
    sample = load_providers_config("providers.sample.json")
    for name in DEFAULT_CHAT_PROVIDER_PRIORITY:
        assert name in sample


def test_sample_file_is_used_when_providers_file_is_missing():
    config = load_providers_config("does_not_exist.json")
    sample = load_providers_config("providers.sample.json")
    assert config == sample


# build_providers() takes the content of providers.json and the environment
# as plain dicts, so these tests don't depend on providers.json or .env.


def test_provider_settings_are_read_from_the_file():
    providers_config = {
        "my_server": {
            "type": "openai",
            "url": "https://example.org/v1",
            "api_key_env": "MY_SERVER_API_KEY",
            "chat_model": "some-model",
        }
    }
    env = {"MY_SERVER_API_KEY": "fake-key"}
    providers = build_providers(providers_config, env)
    expected = {
        "type": "openai",
        "url": "https://example.org/v1",
        "api_key": "fake-key",
        "chat_model": "some-model",
    }
    assert providers["my_server"] == expected


def test_provider_type_defaults_to_ollama():
    providers_config = {"my_server": {"url": "https://example.org"}}
    providers = build_providers(providers_config, env={})
    assert providers["my_server"]["type"] == "ollama"


# llm_manager skips a provider whose api_key is "" (needs a key, but it's missing).
# None means the provider doesn't need a key.


def test_api_key_is_none_when_the_provider_does_not_need_one():
    providers_config = {"my_server": {"url": "https://example.org"}}
    providers = build_providers(providers_config, env={})
    assert providers["my_server"]["api_key"] is None


def test_api_key_is_empty_when_the_provider_needs_one_but_it_is_missing():
    providers_config = {
        "my_server": {"url": "https://example.org", "api_key_env": "MY_SERVER_API_KEY"}
    }
    providers = build_providers(providers_config, env={})
    assert providers["my_server"]["api_key"] == ""


def test_tracing_is_off_when_flag_not_set(monkeypatch):
    """Without LANGFUSE_TRACING_ENABLED in .env, Langfuse must not send traces."""
    # Remove the flag, as if it wasn't in .env. monkeypatch puts the original value back
    # after the test. raising=False: don't fail if the flag wasn't set to begin with.
    monkeypatch.delenv("LANGFUSE_TRACING_ENABLED", raising=False)
    # The missing flag should be set to "false"
    turn_tracing_off_by_default()
    result = os.environ["LANGFUSE_TRACING_ENABLED"]
    assert result == "false"
