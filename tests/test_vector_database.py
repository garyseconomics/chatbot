import pytest
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from config import settings
from rag.vector_database import get_vector_database


@pytest.fixture(scope="module")
def test_database_path():
    return "./tests/chroma_langchain_db"


@pytest.fixture(scope="module")
def embeddings_model():
    embedding_url = settings.providers["ollama_self_hosted"]["url"]
    return OllamaEmbeddings(model=settings.embeddings_model, base_url=embedding_url)


@pytest.fixture(scope="module")
def openrouter_embeddings_model():
    provider = settings.providers["openrouter"]
    return OpenAIEmbeddings(
        model=provider["embeddings_model"],
        base_url=provider["url"],
        api_key=provider["api_key"],
    )


def test_get_vector_database(test_database_path, embeddings_model):
    vector_store = get_vector_database(test_database_path, embeddings_model)
    assert isinstance(vector_store, Chroma)
    assert vector_store._collection.name == settings.collection_name


def test_get_vector_database_with_openrouter_embeddings(test_database_path, openrouter_embeddings_model):
    vector_store = get_vector_database(test_database_path, openrouter_embeddings_model)
    assert isinstance(vector_store, Chroma)
    assert vector_store._collection.name == settings.collection_name