import pytest
import chromadb
from langchain_chroma import Chroma
from vector_database.vector_database import *

test_database_path = './tests/chroma_langchain_db'
collection_name = 'youtube_videos'


def test_get_chromadb_client():
    client = get_chromadb_client(test_database_path)
    assert isinstance(client, chromadb.api.client.Client)

def test_create_database():
    vector_store = create_vector_database(test_database_path)
    client = get_chromadb_client(test_database_path)
    # Verify the returned object is an instance of Chroma
    assert isinstance(vector_store, Chroma)
    collection = client.get_collection(collection_name)
    # Verify the collection has been created
    assert isinstance(collection, chromadb.Collection)
    assert collection.count() > 0

def test_generate_db_with_documents():
    client = get_chromadb_client(test_database_path)
    client.delete_collection(collection_name)
    files_list = ["tests/sample.srt"]
    vector_store = generate_db_with_documents(test_database_path, files_list)
    collection = client.get_collection(collection_name)
    # Verify the collection has been created
    assert isinstance(collection, chromadb.Collection)
    # Verify the collection has two items
    assert collection.count() == 2
    documents = collection.peek()["documents"]
    assert documents[0] == '''Okay. Welcome back to Gary’s Economics. Today we are going to introduce the first part of our online course. Video number one, which is going to be What is Wealth'''

def test_get_collections_from_database():
   collections_list = get_collections_from_database(test_database_path)
   assert len(collections_list) == 1
   assert collections_list[0].name == collection_name

def test_delete_existing_collections():
   # Ensure that there is a collection in the database
   create_vector_database(test_database_path)
   client = get_chromadb_client(test_database_path)
   assert len(client.list_collections()) > 0
   # Delete existing collections
   delete_existing_collections(test_database_path)
   # Test that the collections has been deleted
   assert len(client.list_collections()) == 0

