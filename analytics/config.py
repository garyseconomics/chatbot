from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from config import settings as main_settings

load_dotenv()


class Settings(BaseSettings):
    # Analytics database — SQLite file path
    analytics_db_path: str = "./analytics/analytics.db"

    # Langfuse — read from LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST in .env
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    prompt_version: int = main_settings.prompt_version
    provider_name: str = main_settings.chat_provider_priority[0]
    chat_model: str = main_settings.providers[provider_name]["chat_model"]


settings = Settings()