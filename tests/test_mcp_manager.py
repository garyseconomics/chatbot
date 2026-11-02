import pytest
from mcp.types import CallToolResult, TextContent

from config import settings
from mcp_client.mcp_manager import MCP_query, parse_rag_result

# --- parse_rag_result() tests ---


def test_parse_rag_result_returns_answer():
    """The RAG tool sends its answer as JSON text inside the result content."""
    result = CallToolResult(
        content=[TextContent(type="text", text='{"answer": "A friendly chatbot.", "sources": []}')]
    )

    answer = parse_rag_result(result)

    assert answer == "A friendly chatbot."


def test_parse_rag_result_raises_on_tool_error():
    """When the tool reports an error, raise so the bots show their error message."""
    result = CallToolResult(
        content=[TextContent(type="text", text="Answer generation failed.")], is_error=True
    )

    with pytest.raises(RuntimeError):
        parse_rag_result(result)


# --- End-to-end test (hits the real MCP server in MCP_SERVER_URL) ---


@pytest.mark.mcp_server
@pytest.mark.asyncio
async def test_mcp_query_end_to_end():
    if not settings.mcp_server_url:
        pytest.fail("MCP_SERVER_URL is not set: this test needs a running MCP server")

    response = await MCP_query("What is wealth?", client_type="pytest")

    assert isinstance(response["answer"], str)
    assert len(response["answer"]) > 0
    # MCP_query returns the default error message on failure, so check it's a real answer
    assert response["answer"] != settings.error_messages["DefaultError"]
