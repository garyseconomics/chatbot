from unittest.mock import MagicMock, patch

from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from rag.rag_manager import RAG_query, generate, retrieve

# --- retrieve() tests ---


@patch("rag.rag_manager.get_or_create_vector_database")
def test_retrieve_returns_documents(mock_get_db):
    docs = [Document(page_content="Economy is growing.", metadata={"source": "a.srt"})]
    mock_store = MagicMock()
    mock_store.similarity_search.return_value = docs
    mock_get_db.return_value = mock_store

    state = {"question": "How is the economy?"}
    result = retrieve(state)

    assert result["context"] == docs
    mock_store.similarity_search.assert_called_once_with("How is the economy?")


@patch("rag.rag_manager.get_or_create_vector_database")
def test_retrieve_returns_empty_list_when_no_matches(mock_get_db):
    mock_store = MagicMock()
    mock_store.similarity_search.return_value = []
    mock_get_db.return_value = mock_store

    result = retrieve({"question": "Something obscure"})
    assert result["context"] == []


# --- generate() tests ---


@patch("rag.rag_manager.llm_chat")
def test_generate_returns_answer_from_llm(mock_chat):
    mock_chat.return_value = AIMessage(content="Wealth is assets minus debts.")

    state = {
        "question": "What is wealth?",
        "context": [
            Document(page_content="Wealth means total assets.", metadata={}),
        ],
    }
    result = generate(state)

    assert result["answer"] == "Wealth is assets minus debts."
    mock_chat.assert_called_once()


@patch("rag.rag_manager.llm_chat")
def test_generate_with_empty_context(mock_chat):
    mock_chat.return_value = AIMessage(content="I don't have enough context.")

    state = {"question": "What is wealth?", "context": []}
    result = generate(state)

    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0


# --- RAG_query() tests ---


@patch("rag.rag_manager.llm_chat")
@patch("rag.rag_manager.get_or_create_vector_database")
def test_rag_query_returns_answer(mock_get_db, mock_chat):
    docs = [Document(page_content="Tax the rich.", metadata={"source": "b.srt"})]
    mock_store = MagicMock()
    mock_store.similarity_search.return_value = docs
    mock_get_db.return_value = mock_store
    mock_chat.return_value = AIMessage(content="Yes, we should.")

    response = RAG_query("Should we tax the rich?")

    assert isinstance(response["answer"], str)
    assert response["answer"] == "Yes, we should."


@patch("rag.rag_manager.llm_chat")
@patch("rag.rag_manager.get_or_create_vector_database")
def test_rag_query_returns_error_message_on_failure(mock_get_db, mock_chat):
    mock_get_db.side_effect = Exception("DB connection failed")

    response = RAG_query("Any question")

    assert "sorry" in response["answer"].lower()


# --- End-to-end test (hits real Ollama and vector DB) ---


def test_rag_query_end_to_end():
    question = "What is wealth?"
    response = RAG_query(question)
    assert isinstance(response["answer"], str)
