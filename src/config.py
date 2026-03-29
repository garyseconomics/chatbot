import logging

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env into OS environment so external libraries (Langfuse, etc.)
# that read env vars directly can find them.
load_dotenv()


class Settings(BaseSettings):
    # Pydantic-settings automatically reads env vars matching each field name.
    # For example, ollama_self_hosted reads from OLLAMA_SELF_HOSTED in .env.
    # The values after "=" are defaults used when the env var is not set.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Ollama hosts — read the urls from env vars in .env
    ollama_local_host_url: str = "http://localhost:11434"
    ollama_self_hosted_url: str = ""
    ollama_cloud_url: str = ""

    # Ollama Cloud API key — read from .env
    ollama_cloud_api_key: str = ""

    # LLM settings
    prompt_version: int = 4
    embeddings_model: str = ""

    # Provider priority — try providers in this order, use the first available one.
    # Each name must match a key in the providers property below.
    chat_provider_priority: list[str] = [
        "ollama_cloud",
        "ollama_self_hosted",
        "ollama_local",
    ]

    embeddings_provider_priority: list[str] = [
        "ollama_self_hosted",
        "ollama_local",
    ]

    @property
    def providers(self) -> dict:
        return {
            "ollama_local": {
                "url": self.ollama_local_host_url,
                "api_key": None,
                "chat_model": "qwen3:4b",
            },
            "ollama_self_hosted": {
                "url": self.ollama_self_hosted_url,
                "api_key": None,
                "chat_model": "qwen3:32b",
            },
            "ollama_cloud": {
                "url": self.ollama_cloud_url,
                "api_key": self.ollama_cloud_api_key,
                "chat_model": "qwen3-next:80b",
            },
        }

    # Vector database
    database_path: str = ""
    collection_name: str = ""
    video_ids_separator: str = ""

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

    # Langfuse — read from LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST in .env
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"


settings = Settings()

# Configure logging level based on log_level setting
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    # Convert log_level string (e.g. "INFO") to its logging constant (e.g. logging.INFO = 20)
    level=getattr(logging, settings.log_level.upper(), logging.DEBUG),
)
