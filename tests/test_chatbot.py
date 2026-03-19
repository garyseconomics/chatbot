from unittest.mock import AsyncMock, patch


@patch("interfaces.chatbot.input", return_value="What is wealth?")
@patch("interfaces.chatbot.RAG_query", new_callable=AsyncMock)
def test_chatbot_runs_without_errors(mock_rag, mock_input):
    """The CLI chatbot runs end-to-end without crashing."""
    mock_rag.return_value = {
        "answer": "Wealth is...",
        "context": [],
        "question": "What is wealth?",
    }

    from interfaces.chatbot import main

    main()