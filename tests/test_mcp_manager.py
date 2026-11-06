import pytest
from mcp.types import CallToolResult, TextContent

from knowledge.mcp_manager import parse_tool_result

# --- parse_tool_result() tests ---


def test_parse_tool_result_returns_answer_and_transcript_chunks():
    """The RAG tool sends its result as one object in structured_content."""
    rag_result = {
        "answer": "A friendly chatbot.",
        "transcript_chunks": [{"video_id": "abc123", "text": "Wealth is ownership of assets."}],
    }
    result = CallToolResult(
        content=[TextContent(type="text", text="The same result, as JSON text.")],
        structured_content=rag_result,
    )

    tool_result = parse_tool_result(result)

    assert tool_result == rag_result


def test_parse_tool_result_raises_on_tool_error():
    """When the tool reports an error, raise so the bots show their error message."""
    result = CallToolResult(
        content=[TextContent(type="text", text="Answer generation failed.")], is_error=True
    )

    with pytest.raises(RuntimeError):
        parse_tool_result(result)
