import json

import pytest
from mcp.types import CallToolResult, TextContent

from orchestrator.tool_manager import format_tool_result, parse_tool_result

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


def test_parse_tool_result_returns_empty_dict_without_structured_content():
    """A tool that sends no structured result must not crash the bot."""
    result = CallToolResult(content=[TextContent(type="text", text="Plain text only.")])

    tool_result = parse_tool_result(result)

    assert tool_result == {}


# --- format_tool_result() tests ---


def test_format_tool_result_sends_unknown_results_as_json():
    """The orchestrator AI still sees what a tool found, even when the result's keys are
    unknown and it isn't stored in the knowledge."""
    tool_result = {"new_tool": [{"new_content_id": "abc123", "title": "Why rents go up"}]}

    text = format_tool_result(tool_result)

    assert text == json.dumps(tool_result)
