import pytest
from mcp.types import CallToolResult, TextContent

from knowledge.mcp_manager import parse_tool_result

# --- parse_tool_result() tests ---


def test_parse_tool_result_returns_transcript_chunks():
    """The transcript search tool sends its result as one object in structured_content."""
    search_result = {
        "transcript_chunks": [{"video_id": "abc123", "text": "Wealth is ownership of assets."}],
    }
    result = CallToolResult(
        content=[TextContent(type="text", text="The same result, as JSON text.")],
        structured_content=search_result,
    )

    tool_result = parse_tool_result(result)

    assert tool_result == search_result


def test_parse_tool_result_raises_on_tool_error():
    """When the tool reports an error, raise so the bots show their error message."""
    result = CallToolResult(
        content=[TextContent(type="text", text="Search failed.")], is_error=True
    )

    with pytest.raises(RuntimeError):
        parse_tool_result(result)
