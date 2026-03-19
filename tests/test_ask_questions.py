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
    # Temporal awareness test case (issue #26) — answer depends on current
    # chancellor and economic context, requires date-aware retrieval.
    "Assume a UK chancellor was completely aligned with your analysis and"
    " theory about the economy, how do you think big influential structures"
    " like the Bank of England or the bond markets would react to the"
    " chancellor announcing aggressive wealth taxation policies in the UK?",
]


@pytest.mark.asyncio
async def test_rag_answers_question():
    response = await RAG_query(questions_list[0], user_id="test")
    assert isinstance(response["answer"], str)
    assert len(response["answer"]) > 0
