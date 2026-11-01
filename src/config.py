import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env into OS environment so external libraries (Langfuse, etc.)
# that read env vars directly can find them.
load_dotenv()


def turn_tracing_off_by_default() -> None:
    """Keep Langfuse tracing off unless LANGFUSE_TRACING_ENABLED=true is set in .env.

    The Langfuse library treats a missing flag as "on", and the @observe decorators read
    it directly from the environment, so the default has to be set here.
    """
    os.environ.setdefault("LANGFUSE_TRACING_ENABLED", "false")


turn_tracing_off_by_default()


# LLM providers are configured in providers.json (not in the repo, because it can list
# private servers). Their API keys and the order to try them in are set in .env.
PROVIDERS_FILE = "providers.json"
# Used when providers.json doesn't exist, e.g. in a fresh clone of the repo.
PROVIDERS_SAMPLE_FILE = "providers.sample.json"


def load_providers_config(path=PROVIDERS_FILE, fallback=PROVIDERS_SAMPLE_FILE) -> dict:
    if not Path(path).exists():
        path = fallback
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_providers(providers_config, env) -> dict:
    """Combine each provider's settings from providers.json with its API key from the env.

    The key is read from the env variable named in the provider's api_key_env:
    for example, "api_key_env": "OLLAMA_CLOUD_API_KEY".
    """
    providers = {}
    for name, provider in providers_config.items():
        # api_key_env is null for providers that don't need a key (e.g. a local Ollama).
        api_key_env = provider.get("api_key_env")
        providers[name] = {
            # "ollama", or "openai" for any OpenAI-compatible API (e.g. OpenRouter)
            "type": provider.get("type", "ollama"),
            "url": provider.get("url", ""),
            # api_key=None means the provider doesn't need a key;
            # api_key="" means it needs one but it's missing.
            "api_key": None if api_key_env is None else env.get(api_key_env, ""),
            "chat_model": provider.get("chat_model", ""),
        }
    return providers


providers_config = load_providers_config()

# Used when CHAT_PROVIDER_PRIORITY is not set in .env.
# Each name must match a provider in providers.sample.json.
DEFAULT_CHAT_PROVIDER_PRIORITY = ["ollama_cloud", "ollama_local"]


class Settings(BaseSettings):
    # Pydantic-settings automatically reads env vars matching each field name.
    # For example, telegram_token reads from TELEGRAM_TOKEN in .env.
    # The values after "=" are defaults used when the env var is not set.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM settings
    prompt_version: int = 4

    # Provider priority — try providers in this order, use the first available one.
    # Read from CHAT_PROVIDER_PRIORITY in .env, written as a JSON list.
    # Each name must match a provider in providers.json.
    chat_provider_priority: list[str] = DEFAULT_CHAT_PROVIDER_PRIORITY

    # The only provider used by the tests that call an LLM — read from TEST_CHAT_PROVIDER.
    test_chat_provider: str = "ollama_cloud"

    @property
    def providers(self) -> dict:
        return build_providers(providers_config, os.environ)

    # MCP server — read from MCP_SERVER_URL in .env
    mcp_server_url: str = ""

    # App
    app_name: str = "GarysEconomics_bot"
    log_level: str = "INFO"
    bot_greeting: str = (
        "I'm back online! We're still in the testing phase, "
        "so I may restart from time to time. Feel free to keep asking questions."
    )
    discord_channel: str = "youtube-chatbot"

    # User-facing error messages — keyed by exception class name.
    error_messages: dict[str, str] = {
        "ConnectionError": "I can't reach the AI service right now. Please try again later.",
        "ResponseError": "The AI service is not working properly.",
        "ValueError": "There's a configuration problem. Please contact the admin.",
        "DefaultError": "I'm having some technical problems. Please try again later.",
    }

    # Bot tokens — read from TELEGRAM_TOKEN and DISCORD_TOKEN in .env
    telegram_token: str = ""
    discord_token: str = ""

    # Bot message limits - read from TELEGRAM_MESSAGE_LIMIT and DISCORD_MESSAGE_LIMIT in .env
    telegram_message_limit: int = 4096
    discord_message_limit: int = 2000

    # Langfuse — read from LANGFUSE_TRACING_ENABLED, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY
    # and LANGFUSE_TEST_TRACING_ENVIRONMENT in .env
    # (LANGFUSE_BASE_URL, LANGFUSE_TRACING_ENVIRONMENT and OTEL_SERVICE_NAME are read by the
    # Langfuse library directly)
    langfuse_tracing_enabled: bool = False
    # Read from LANGFUSE_MESSAGE_TRACING_ENABLED. Sends the questions and answers to Langfuse.
    # Read once at startup, when the @observe decorators are created.
    langfuse_message_tracing_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    # Replaces LANGFUSE_TRACING_ENVIRONMENT while running pytest (see tests/conftest.py)
    langfuse_test_tracing_environment: str = "automated_tests"


settings = Settings()

# Configure logging level based on log_level setting
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    # Convert log_level string (e.g. "INFO") to its logging constant (e.g. logging.INFO = 20)
    level=getattr(logging, settings.log_level.upper(), logging.DEBUG),
)
