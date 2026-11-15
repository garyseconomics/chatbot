from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from config import settings
from orchestrator.orchestrator import answer_question, trim_conversation
from orchestrator.tools_info import SELECT_INFO_TOOL

# --- trim_conversation() (no LLM, no MCP server) ---


def make_conversation(turns) -> list:
    """A conversation with the given number of turns: Question 1, Answer 1, Question 2, ..."""
    conversation = []
    for turn in range(1, turns + 1):
        conversation.append(HumanMessage(content=f"Question {turn}"))
        conversation.append(AIMessage(content=f"Answer {turn}"))
    return conversation


def test_trim_conversation_with_0_turns_forgets_everything(monkeypatch):
    monkeypatch.setattr(settings, "conversation_turns", 0)
    conversation = make_conversation(1)

    trim_conversation(conversation)

    assert conversation == []


def test_trim_conversation_with_1_turn_keeps_the_last_turn(monkeypatch):
    monkeypatch.setattr(settings, "conversation_turns", 1)
    conversation = make_conversation(2)

    trim_conversation(conversation)

    assert conversation == [HumanMessage(content="Question 2"), AIMessage(content="Answer 2")]


def test_trim_conversation_with_3_turns_keeps_the_last_3_turns(monkeypatch):
    monkeypatch.setattr(settings, "conversation_turns", 3)
    conversation = make_conversation(4)

    trim_conversation(conversation)

    assert conversation == [
        HumanMessage(content="Question 2"),
        AIMessage(content="Answer 2"),
        HumanMessage(content="Question 3"),
        AIMessage(content="Answer 3"),
        HumanMessage(content="Question 4"),
        AIMessage(content="Answer 4"),
    ]


# --- answer_question() when the MCP server can't be reached ---


@pytest.mark.asyncio
async def test_answer_question_keeps_the_error_in_the_conversation(monkeypatch):
    """The error message the user sees is added to the conversation, like any other answer."""
    # Nothing listens on port 1, so the connection fails straight away (no network needed)
    monkeypatch.setattr(settings, "mcp_server_url", "http://127.0.0.1:1/mcp")
    conversation = [HumanMessage(content="What is wealth?")]

    await answer_question(conversation, {}, client_type="pytest")

    assert conversation == [
        HumanMessage(content="What is wealth?"),
        AIMessage(content=settings.error_messages["DefaultError"]),
    ]


# --- The cap on tool rounds (hits the LLM, not the MCP server) ---


@pytest.mark.asyncio
async def test_answer_question_without_tool_rounds_answers_from_the_conversation(monkeypatch):
    """With max_tool_rounds at 0 the orchestrator AI never runs, so no tool is called and
    the chat AI answers from the conversation alone."""
    monkeypatch.setattr(settings, "max_tool_rounds", 0)
    # Nothing listens on port 1: if a tool were called, the answer would be the error message
    monkeypatch.setattr(settings, "mcp_server_url", "http://127.0.0.1:1/mcp")
    conversation = [HumanMessage(content="What is wealth?")]
    knowledge = {}

    answer = await answer_question(conversation, knowledge, client_type="pytest")

    assert answer != settings.error_messages["DefaultError"]
    assert knowledge == {}


# --- The knowledge flag (hits the LLM; the MCP server is mocked) ---

FAKE_SEARCH_TOOL = {
    "name": "search_transcripts",
    "description": "Search Gary's Economics video transcripts.",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}


@pytest.mark.asyncio
async def test_answer_question_with_knowledge_off_stores_nothing(monkeypatch):
    """With store_in_knowledge off, a tool runs and the bot answers, but the knowledge stays
    empty."""
    monkeypatch.setattr(settings, "store_in_knowledge", False)
    mock_get_tools = AsyncMock(return_value=[FAKE_SEARCH_TOOL, SELECT_INFO_TOOL])
    monkeypatch.setattr("orchestrator.orchestrator.get_tools_list", mock_get_tools)
    tool_result = {"transcript_chunks": [{"video_id": "v1", "text": "Wealth is..."}]}
    mock_call_tool = AsyncMock(return_value=tool_result)
    monkeypatch.setattr("orchestrator.orchestrator.call_tool", mock_call_tool)
    conversation = [HumanMessage(content="What is wealth?")]
    knowledge = {}

    answer = await answer_question(conversation, knowledge, client_type="pytest")

    assert mock_call_tool.called
    assert answer != settings.error_messages["DefaultError"]
    assert knowledge == {}


# --- The conversation turns (the MCP server and the LLMs are mocked) ---


@pytest.mark.asyncio
async def test_answer_question_remembers_only_the_last_turn(monkeypatch):
    """With conversation_turns at 1, after two questions only the second turn is left."""
    monkeypatch.setattr(settings, "conversation_turns", 1)
    monkeypatch.setattr("orchestrator.orchestrator.retrieve_info", AsyncMock(return_value={}))
    monkeypatch.setattr("orchestrator.orchestrator.generate_answer", AsyncMock(return_value="Hi"))
    conversation = []

    conversation.append(HumanMessage(content="What is wealth?"))
    await answer_question(conversation, {}, client_type="pytest")
    conversation.append(HumanMessage(content="What is inequality?"))
    await answer_question(conversation, {}, client_type="pytest")

    assert conversation == [HumanMessage(content="What is inequality?"), AIMessage(content="Hi")]


# --- End-to-end tests (hit the real MCP server in MCP_SERVER_URL) ---


@pytest.mark.mcp_server
@pytest.mark.asyncio
async def test_answer_question_keeps_a_two_turn_conversation():
    """After two questions, the conversation holds both questions and both answers, and the
    knowledge holds what the tool retrieved."""
    if not settings.mcp_server_url:
        pytest.fail("MCP_SERVER_URL is not set: this test needs a running MCP server")
    conversation = []
    knowledge = {}

    conversation.append(HumanMessage(content="What is wealth?"))
    await answer_question(conversation, knowledge, client_type="pytest")
    conversation.append(HumanMessage(content="Tell me more"))
    await answer_question(conversation, knowledge, client_type="pytest")

    message_types = [type(message) for message in conversation]
    assert message_types == [HumanMessage, AIMessage, HumanMessage, AIMessage]
    # Both answers are real answers, not the default error message
    assert conversation[1].content != settings.error_messages["DefaultError"]
    assert conversation[3].content != settings.error_messages["DefaultError"]
    # Only checks that something was stored: the structure of knowledge will change
    assert knowledge


@pytest.mark.mcp_server
@pytest.mark.asyncio
async def test_answer_question_with_0_turns_and_no_previous_knowledge_still_answers(monkeypatch):
    """With conversation_turns at 0, the bot remembers nothing but still answers each question."""
    if not settings.mcp_server_url:
        pytest.fail("MCP_SERVER_URL is not set: this test needs a running MCP server")
    monkeypatch.setattr(settings, "conversation_turns", 0)
    monkeypatch.setattr(settings, "store_in_knowledge", False)
    conversation = []

    conversation.append(HumanMessage(content="What is wealth?"))
    first_answer = await answer_question(conversation, {}, client_type="pytest")
    conversation.append(HumanMessage(content="What is inequality?"))
    second_answer = await answer_question(conversation, {}, client_type="pytest")

    assert first_answer != settings.error_messages["DefaultError"]
    assert second_answer != settings.error_messages["DefaultError"]
    assert conversation == []
