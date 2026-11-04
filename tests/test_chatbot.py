from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
@patch("interfaces.chatbot.input", side_effect=["What is wealth?", "Tell me more", "quit"])
@patch("interfaces.chatbot.answer_question", new_callable=AsyncMock)
async def test_chatbot_runs_without_errors(mock_answer, mock_input):
    """The CLI chatbot runs end-to-end without crashing."""
    mock_answer.return_value = "Wealth is..."

    from interfaces.chatbot import main

    await main()
