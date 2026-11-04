import json
import logging
from importlib.metadata import version

from langchain_core.messages import AIMessage
from langfuse import observe
from mcp import Client, Implementation

from config import settings

logger = logging.getLogger(__name__)

RAG_TOOL_NAME = "retrieval_augmented_generation"
CHATBOT_VERSION = version("garys-economics-chatbot")


def parse_tool_result(result) -> dict:
    """Return the answer and sources from the tool result, or raise if it reported an error."""
    text = result.content[0].text
    if result.is_error:
        raise RuntimeError(f"MCP tool error: {text}")
    # The tool sends its answer as JSON text: {"answer": ..., "sources": [...]}
    return json.loads(text)


def add_new_transcripts(knowledge, sources) -> None:
    """Add to the knowledge only the transcripts it doesn't have yet."""
    if "transcripts" not in knowledge:
        knowledge["transcripts"] = []
    for source in sources:
        if source not in knowledge["transcripts"]:
            knowledge["transcripts"].append(source)


# A span of its own in the trace, so its input (the query) and output (what the tool
# returned) can be checked for each tool call.
@observe(
    name="call_tool",
    capture_input=settings.langfuse_message_tracing_enabled,
    capture_output=settings.langfuse_message_tracing_enabled,
)
async def call_tool(tool_name, arguments, client_type) -> dict:
    """Call a tool on the MCP server and return its parsed result."""
    # The MCP server records the client name (e.g. telegram_chatbot) in its traces.
    client_info = Implementation(name=f"{client_type}_chatbot", version=CHATBOT_VERSION)
    async with Client(settings.mcp_server_url, client_info=client_info) as client:
        result = await client.call_tool(tool_name, arguments)
    return parse_tool_result(result)


@observe(
    name=settings.app_name,
    capture_input=settings.langfuse_message_tracing_enabled,
    capture_output=settings.langfuse_message_tracing_enabled,
)
async def answer_question(conversation, knowledge, client_type) -> str:
    """Answer the last question in the conversation, and add the answer to the conversation
    and the new transcripts to the knowledge."""
    try:
        # Temporary: the whole conversation is the query. Later the orchestrator writes it.
        tool_result = await call_tool(RAG_TOOL_NAME, {"query": str(conversation)}, client_type)
        answer = tool_result["answer"]
        add_new_transcripts(knowledge, tool_result["sources"])
    except Exception as e:
        logger.error("MCP query failed (%s): %s", type(e).__name__, e)
        answer = settings.error_messages["DefaultError"]
    # The error message is also kept, so the conversation is the same as the user sees it
    conversation.append(AIMessage(content=answer))
    return answer
