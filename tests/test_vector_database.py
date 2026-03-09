import pytest
import chromadb
from langchain_chroma import Chroma
from vector_database.vector_database_manager import *
from config import settings

test_database_path = './tests/chroma_langchain_db'


def test_get_chromadb_client():
    client = get_chromadb_client(test_database_path)
    assert isinstance(client, chromadb.api.client.Client)

def test_get_or_create_database():
    client = get_chromadb_client(test_database_path)
    # Verify there are no previous collections created
    assert len(client.list_collections()) == 0
    # Create the database and collection
    vector_store = get_or_create_vector_database(test_database_path)
    # Verify the returned object is an instance of Chroma
    assert isinstance(vector_store, Chroma)
    collection = client.get_collection(settings.collection_name)
    # Verify the collection has been created
    assert isinstance(collection, chromadb.Collection)
    assert len(client.list_collections()) == 1

def test_add_documents_to_vector_database():
    client = get_chromadb_client(test_database_path)
    client.delete_collection(settings.collection_name)
    files_list = ["tests/sample.srt"]
    vector_store = add_documents_to_vector_database(test_database_path, files_list)
    collection = client.get_collection(settings.collection_name)
    # Verify the collection has been created
    assert isinstance(collection, chromadb.Collection)
    # Verify the collection has two items
    assert collection.count() == 1
    documents = collection.peek()["documents"]
    expected_content = '''Okay. Welcome back to Gary’s Economics. Today we are going to introduce the first part of our online course. Video number one, which is going to be What is Wealth. Okay so I was at a conference the other day, a conference about economics media, and there was a guy who basically spoke about how when people watch Jordan Peterson's videos, they don't just watch his recent videos, they go back to the beginning and they watch it through.'''
    assert documents[0] == expected_content

def test_get_collections_from_database():
   collections_list = get_collections_from_database(test_database_path)
   assert len(collections_list) == 1
   assert collections_list[0].name == settings.collection_name

def test_delete_existing_collections():
   # Ensure that there is a collection in the database
   get_or_create_vector_database(test_database_path)
   client = get_chromadb_client(test_database_path)
   assert len(client.list_collections()) > 0
   # Delete existing collections
   delete_existing_collections(test_database_path)
   # Test that the collections has been deleted
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

