from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # Analytics database — SQLite file path
    analytics_db_path: str = "./analytics/analytics.db"

    # Langfuse — read from LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST in .env
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    prompt_version: str = "4"
    chat_model: str = "qwen3-next:80b"


settings = Settings()