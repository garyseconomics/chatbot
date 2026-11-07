from langfuse import get_client, observe
from mcp import Client, Implementation

from config import settings
from orchestrator.tools_info import EXCLUDED_TOOL_NAMES, WRITE_ANSWER_TOOL


def parse_tool_result(result) -> dict:
    """Return the tool's result object, or raise if it reported an error."""
    if result.is_error:
        raise RuntimeError(f"MCP tool error: {result.content[0].text}")
    return result.structured_content


def format_tool_result(tool_result) -> str:
    """The tool's result as text, for the orchestrator AI's tool message."""
    # Only the text goes to the orchestrator AI for now, not the video_id
    chunk_texts = [chunk["text"] for chunk in tool_result.get("transcript_chunks", [])]
    return "\n\n".join(chunk_texts)


def get_client_info(client_type) -> Implementation:
    # The MCP server records the client name (e.g. telegram_chatbot) in its traces.
    return Implementation(name=f"{client_type}_chatbot", version=settings.app_version)


async def list_mcp_tools(client_type) -> list[dict]:
    """Get the MCP server's tools, in the format the LLM expects (name, description, parameters)."""
    async with Client(settings.mcp_server_url, client_info=get_client_info(client_type)) as client:
        result = await client.list_tools()
    return [
        {"name": tool.name, "description": tool.description, "parameters": tool.input_schema}
        for tool in result.tools
    ]


async def get_tools_list(client_type) -> list[dict]:
    """The tools the orchestrator AI can call: the MCP server's tools (except the excluded
    ones) and write_answer."""
    mcp_tools = await list_mcp_tools(client_type)
    allowed_tools = [tool for tool in mcp_tools if tool["name"] not in EXCLUDED_TOOL_NAMES]
    return allowed_tools + [WRITE_ANSWER_TOOL]


# A span of its own in the trace, so its input (the arguments) and output (what the tool
# returned) can be checked for each tool call.
@observe(
    name="call_tool",
    capture_input=settings.langfuse_message_tracing_enabled,
    capture_output=settings.langfuse_message_tracing_enabled,
)
async def call_tool(tool_name, arguments, client_type) -> dict:
    """Call a tool on the MCP server and return its parsed result."""
    # Name the span after the tool, so the trace shows which tool was called
    get_client().update_current_span(name=f"call_tool: {tool_name}")
    async with Client(settings.mcp_server_url, client_info=get_client_info(client_type)) as client:
        result = await client.call_tool(tool_name, arguments)
    return parse_tool_result(result)
