from langfuse import get_client, observe
from mcp import Client, Implementation

from config import settings


def parse_tool_result(result) -> dict:
    """Return the tool's result object, or raise if it reported an error."""
    if result.is_error:
        raise RuntimeError(f"MCP tool error: {result.content[0].text}")
    return result.structured_content


def get_client_info(client_type) -> Implementation:
    # The MCP server records the client name (e.g. telegram_chatbot) in its traces.
    return Implementation(name=f"{client_type}_chatbot", version=settings.app_version)


async def list_tools(client_type) -> list[dict]:
    """Get the MCP server's tools, in the format the LLM expects (name, description, parameters)."""
    async with Client(settings.mcp_server_url, client_info=get_client_info(client_type)) as client:
        result = await client.list_tools()
    return [
        {"name": tool.name, "description": tool.description, "parameters": tool.input_schema}
        for tool in result.tools
    ]


# A span of its own in the trace, so its input (the query) and output (what the tool
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
