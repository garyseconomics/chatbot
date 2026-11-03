import pytest
from langchain_core.messages import HumanMessage
from mcp.types import CallToolResult, TextContent

from config import settings
from mcp_client.mcp_manager import answer_question, parse_tool_result

# --- parse_tool_result() tests ---


def test_parse_tool_result_returns_answer_and_sources():
    """The RAG tool sends its answer as JSON text inside the result content."""
    result = CallToolResult(
        content=[TextContent(type="text", text='{"answer": "A friendly chatbot.", "sources": []}')]
    )

    tool_result = parse_tool_result(result)

    assert tool_result == {"answer": "A friendly chatbot.", "sources": []}


def test_parse_tool_result_raises_on_tool_error():
    """When the tool reports an error, raise so the bots show their error message."""
    result = CallToolResult(
        content=[TextContent(type="text", text="Answer generation failed.")], is_error=True
    )

    with pytest.raises(RuntimeError):
        parse_tool_result(result)


# --- End-to-end test (hits the real MCP server in MCP_SERVER_URL) ---


@pytest.mark.mcp_server
@pytest.mark.asyncio
async def test_answer_question_end_to_end():
    if not settings.mcp_server_url:
        pytest.fail("MCP_SERVER_URL is not set: this test needs a running MCP server")

    conversation = [HumanMessage(content="What is wealth?")]
    answer = await answer_question(conversation, {}, client_type="pytest")

    assert isinstance(answer, str)
    assert len(answer) > 0
    # answer_question returns the default error message on failure, so check it's a real answer
    assert answer != settings.error_messages["DefaultError"]
