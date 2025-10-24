import pytest
from RAG_manager import RAG_query

def test_RAG_query():
	question = "What is wealth?"
	response = RAG_query(question)
	assert isinstance(response['answer'],str)
