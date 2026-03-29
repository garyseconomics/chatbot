from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from config import settings as main_settings

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Ollama hosts
    ollama_local_host_url: str = "http://localhost:11434"
    ollama_self_hosted_url: str = ""

    # Vector database
    embeddings_model: str = main_settings.embeddings_model
    database_path: str = ""
    collection_name: str = main_settings.collection_name
    chunk_size: int = 1024
    chunk_overlap: int = 105
    batch_size: int = 10

    # Documents
    documents_directory: str = "content_database/docs/import"
    video_ids_separator: str = main_settings.video_ids_separator


settings = Settings()
