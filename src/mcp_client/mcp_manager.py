import json
import logging
from importlib.metadata import version

from langfuse import observe
from mcp import Client, Implementation

from config import settings

logger = logging.getLogger(__name__)

RAG_TOOL_NAME = "retrieval_augmented_generation"
CHATBOT_VERSION = version("garys-economics-chatbot")


def parse_rag_result(result) -> str:
    """Return the answer from the RAG tool result, or raise if the tool reported an error."""
    text = result.content[0].text
    if result.is_error:
        raise RuntimeError(f"MCP tool error: {text}")
    # The tool sends its answer as JSON text: {"answer": ..., "sources": [...]}
    return json.loads(text)["answer"]


@observe(
    name=settings.app_name,
    capture_input=settings.langfuse_message_tracing_enabled,
    capture_output=settings.langfuse_message_tracing_enabled,
)
async def MCP_query(question, client_type) -> dict:
    # The MCP server records the client name (e.g. telegram_chatbot) in its traces.
    client_info = Implementation(name=f"{client_type}_chatbot", version=CHATBOT_VERSION)
    try:
        async with Client(settings.mcp_server_url, client_info=client_info) as client:
            result = await client.call_tool(RAG_TOOL_NAME, {"query": question})
        answer = parse_rag_result(result)
        # context stays empty until the MCP server has a tool for video links
        return {"question": question, "context": [], "answer": answer}
    except Exception as e:
        logger.error("MCP query failed (%s): %s", type(e).__name__, e)
        return {
            "question": question,
            "context": [],
            "answer": settings.error_messages["DefaultError"],
        }
