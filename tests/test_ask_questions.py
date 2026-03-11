import pytest
from rag.rag_manager import RAG_query

questions_list = [
    "What is wealth?",
    "If we tax the rich, will they leave?",
    "How to fix the economy?",
    "Who is Gary?",
    "Tell me about the channel",
    "What is Gary's opinion about the Labour party?",
    "Hi Gary!",
]


@pytest.mark.parametrize("question", questions_list)
def test_rag_answers_question(question):
    response = RAG_query(question)
    assert isinstance(response["answer"], str)
    assert len(response["answer"]) > 0
