import chromadb
import pytest
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from content_database.config import settings
from content_database.scripts.vector_database_manager import (
    add_documents_to_vector_database,
    delete_existing_collections,
    get_chromadb_client,
    get_collections_from_database,
    get_or_create_vector_database,
    process_in_batches,
)


@pytest.fixture(scope="module")
def test_database_path():
    return "./tests/chroma_langchain_db"


@pytest.fixture(scope="module")
def embeddings_model():
    embedding_url = settings.ollama_self_hosted_url
    return OllamaEmbeddings(model=settings.embeddings_model, base_url=embedding_url)


@pytest.fixture(autouse=True)
def clean_database(test_database_path):
    """Delete all collections before each test for isolation."""
    client = get_chromadb_client(test_database_path)
    for collection in client.list_collections():
        client.delete_collection(collection.name)
    yield
    # Clean up after each test too
    client = get_chromadb_client(test_database_path)
    for collection in client.list_collections():
        client.delete_collection(collection.name)


def test_get_chromadb_client(test_database_path):
    client = get_chromadb_client(test_database_path)
    assert isinstance(client, chromadb.api.client.Client)


def test_get_or_create_database(test_database_path, embeddings_model):
    client = get_chromadb_client(test_database_path)
    assert len(client.list_collections()) == 0
    vector_store = get_or_create_vector_database(test_database_path, embeddings_model)
    assert isinstance(vector_store, Chroma)
    collection = client.get_collection(settings.collection_name)
    assert isinstance(collection, chromadb.Collection)
    assert len(client.list_collections()) == 1


def test_add_documents_to_vector_database(test_database_path, embeddings_model):
    files_list = ["content_database/scripts/tests/sample.srt"]
    add_documents_to_vector_database(test_database_path, files_list, embeddings_model)
    client = get_chromadb_client(test_database_path)
    collection = client.get_collection(settings.collection_name)
    assert isinstance(collection, chromadb.Collection)
    assert collection.count() == 1
    documents = collection.peek()["documents"]
    expected_content = (
        "Okay. Welcome back to Gary\u2019s Economics. Today we are"
        " going to introduce the first part of our online course."
        " Video number one, which is going to be What is Wealth."
        " Okay so I was at a conference the other day, a conference"
        " about economics media, and there was a guy who basically"
        " spoke about how when people watch Jordan Peterson's"
        " videos, they don't just watch his recent videos, they"
        " go back to the beginning and they watch it through."
    )
    assert documents[0] == expected_content


def test_add_documents_without_embeddings_model(test_database_path):
    files_list = ["content_database/scripts/tests/sample.srt"]
    vector_store = add_documents_to_vector_database(test_database_path, files_list)
    assert isinstance(vector_store, Chroma)


def test_get_collections_from_database(test_database_path, embeddings_model):
    # Create a collection first
    get_or_create_vector_database(test_database_path, embeddings_model)
    collections_list = get_collections_from_database(test_database_path)
    assert len(collections_list) == 1
    assert collections_list[0].name == settings.collection_name


def test_delete_existing_collections(test_database_path, embeddings_model):
    # Create a collection first
    get_or_create_vector_database(test_database_path, embeddings_model)
    client = get_chromadb_client(test_database_path)
    assert len(client.list_collections()) > 0
    delete_existing_collections(test_database_path)
    assert len(client.list_collections()) == 0


# --- process_in_batches() tests ---


def test_process_in_batches_handles_remainder():
    items = list(range(7))
    batches = list(process_in_batches(items, batch_size=3))
    assert len(batches) == 3
    assert batches[0] == [0, 1, 2]
    assert batches[1] == [3, 4, 5]
    assert batches[2] == [6]


def test_process_in_batches_empty_list():
    batches = list(process_in_batches([], batch_size=5))
    assert batches == []

