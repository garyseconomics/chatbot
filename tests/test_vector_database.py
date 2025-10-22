import pytest
from langchain_chroma import Chroma
from vector_database.vector_database import create_vector_database


def test_returned_instance_type():
    vector_store = create_vector_database()
    # Verify the returned object is an instance of `Chroma`
    assert isinstance(vector_store, Chroma)