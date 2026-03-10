from unittest.mock import MagicMock, patch

from langchain_core.documents import Document


@patch("interfaces.chatbot.input", return_value="What is inflation?")
@patch("interfaces.chatbot.print")
@patch("interfaces.chatbot.RAG_query")
def test_chatbot_prints_greeting_and_answer(mock_rag, mock_print, mock_input):
    """The chatbot prints the greeting, asks for input, and prints the RAG answer."""
    mock_rag.return_value = {
        "answer": "Inflation is rising prices.",
        "context": [],
        "question": "What is inflation?",
    }

    from interfaces.chatbot import main

    main()

    # First print call is the greeting, second is the answer
    assert mock_print.call_count == 2
    greeting = mock_print.call_args_list[0][0][0]
    assert isinstance(greeting, str)
    answer = mock_print.call_args_list[1][0][0]
    assert answer == "Inflation is rising prices."


@patch("interfaces.chatbot.input", return_value="What is inflation?")
@patch("interfaces.chatbot.print")
@patch("interfaces.chatbot.RAG_query")
def test_chatbot_calls_rag_with_user_question(mock_rag, mock_print, mock_input):
    """The chatbot passes the user's question to RAG_query."""
    mock_rag.return_value = {
        "answer": "Answer",
        "context": [],
        "question": "What is inflation?",
    }

    from interfaces.chatbot import main

    main()

    mock_rag.assert_called_once_with("What is inflation?")


@patch("interfaces.chatbot.input", return_value="Tell me about GDP")
@patch("interfaces.chatbot.print")
@patch("interfaces.chatbot.RAG_query")
def test_chatbot_prints_video_links(mock_rag, mock_print, mock_input):
    """When RAG returns context with documents, the chatbot prints video links."""
    mock_rag.return_value = {
        "answer": "GDP measures output.",
        "context": [
            Document(page_content="...", metadata={"source": "abc123_en.srt"}),
        ],
        "question": "Tell me about GDP",
    }

    from interfaces.chatbot import main

    main()

    # greeting, answer, video links
    assert mock_print.call_count == 3
    video_text = mock_print.call_args_list[2][0][0]
    assert "youtube.com" in video_text


@patch("interfaces.chatbot.input", return_value="question")
@patch("interfaces.chatbot.print")
@patch("interfaces.chatbot.RAG_query")
def test_chatbot_skips_video_text_when_no_context(mock_rag, mock_print, mock_input):
    """When RAG returns no context, no video links line is printed."""
    mock_rag.return_value = {
        "answer": "No info available.",
        "context": [],
        "question": "question",
    }

    from interfaces.chatbot import main

    main()

    # Only greeting and answer — no video links printed
    assert mock_print.call_count == 2