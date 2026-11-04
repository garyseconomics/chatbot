import pytest
from mcp.types import CallToolResult, TextContent

from knowledge.mcp_manager import parse_tool_result

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
