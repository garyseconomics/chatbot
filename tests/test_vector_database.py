import pytest
from langchain_chroma import Chroma
from vector_database.vector_database import *

test_database_path = './tests/chroma_langchain_db'

def test_create_database():
    vector_store = create_vector_database(test_database_path)
    # Verify the returned object is an instance of Chroma
    assert isinstance(vector_store, Chroma)

def test_generate_db_with_documents():
    files_list = ["docs/sample.srt"]
    vector_database = generate_db_with_documents(test_database_path, files_list)
    assert isinstance(vector_store, Chroma)