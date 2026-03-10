import logging

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env into OS environment so external libraries (Langfuse, etc.)
# that read env vars directly can find them.
load_dotenv()


class Settings(BaseSettings):
    # Pydantic-settings automatically reads env vars matching each field name.
    # For example, ollama_host_remote reads from OLLAMA_HOST_REMOTE in .env.
    # The values after "=" are defaults used when the env var is not set.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Ollama hosts — read from OLLAMA_HOST_LOCAL and OLLAMA_HOST_REMOTE in .env
    ollama_host_local: str = "http://localhost:11434"
    ollama_host_remote: str = ""

    # LLM settings
    remote_llm: str = "qwen3:32b"
    local_llm: str = "qwen3:4b"
    embedding_model: str = "qwen3-embedding:8b"
    provider: str = "ollama"

    # Vector database
    database_path: str = "./vector_database/chroma_langchain_db"
    collection_name: str = "youtube_videos"
    chunk_size: int = 1024
    chunk_overlap: int = 105
    batch_size: int = 10

    # Documents
    documents_directory: str = "docs/import"
    video_ids_separator: str = "__"

    # App
    app_name: str = "GarysEconomics_bot"
    log_level: str = "DEBUG"
    bot_greeting: str = (
        "Hello. This is Garys Economics Youtube chatbot. "
        "You can ask me questions and I'll answer them using the content of our videos."
    )
    discord_channel: str = "github"

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
