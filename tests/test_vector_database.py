import pytest
from langchain_chroma import Chroma
from vector_database.vector_database import *

test_database_path = './tests/chroma_langchain_db'

def test_create_database():
    vector_store = create_vector_database(test_database_path)
    # Verify the returned object is an instance of Chroma
    assert isinstance(vector_store, Chroma)

def test_add_documents_to_database_empty():
    splits = [""]
    collection = add_documents_to_database(test_database_path, splits)
    assert isinstance(collection, chromadb.Collection)
    assert collection.name == "youtube_videos"
    documents = collection.get()['documents']
    assert documents[0] == ""

def test_add_documents_to_database_with_text():
    splits = ["split 1", "split 2"]
    collection = add_documents_to_database(test_database_path, splits)
    documents = collection.get()['documents']
    assert documents[1] == "split 1"
    assert documents[2] == "split 2"