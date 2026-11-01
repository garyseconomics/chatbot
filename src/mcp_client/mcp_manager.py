import json
import logging

from langfuse import observe
from mcp import Client

from config import settings

logger = logging.getLogger(__name__)

RAG_TOOL_NAME = "retrieval_augmented_generation"


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
    # Pending: client_type (telegram, discord, cli) is not sent to Langfuse yet.
    try:
        async with Client(settings.mcp_server_url) as client:
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
