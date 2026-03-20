import pytest

from rag.rag_manager import RAG_query
from tests.questions_for_testing import questions_list


@pytest.mark.asyncio
async def test_rag_answers_question(use_ollama_for_testing):
    response = await RAG_query(questions_list[0], user_id="test")
    assert isinstance(response["answer"], str)
    assert len(response["answer"]) > 0
