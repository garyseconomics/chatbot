import json
import logging

from langfuse import observe
from mcp import Client

from config import settings
from rag.langfuse_helpers import create_langfuse_client

logger = logging.getLogger(__name__)

RAG_TOOL_NAME = "retrieval_augmented_generation"


def parse_rag_result(result) -> str:
    """Return the answer from the RAG tool result, or raise if the tool reported an error."""
    text = result.content[0].text
    if result.is_error:
        raise RuntimeError(f"MCP tool error: {text}")
    # The tool sends its answer as JSON text: {"answer": ..., "sources": [...]}
    return json.loads(text)["answer"]


def update_and_flush_trace(langfuse_client, client_type) -> None:
    """Update the current Langfuse trace with the client type (telegram, discord, cli)."""
    if not langfuse_client:
        return
    # Pending: Client_type is stored in Langfuse's user_id field for now.
    # Change it to a proper client_type field when we redesign the tracking.
    langfuse_client.update_current_trace(name=settings.app_name, user_id=client_type)
    langfuse_client.flush()


@observe(name=settings.app_name)
async def MCP_query(question, client_type) -> dict:
    langfuse_client = create_langfuse_client()
    try:
        async with Client(settings.mcp_server_url) as client:
            result = await client.call_tool(RAG_TOOL_NAME, {"query": question})
        answer = parse_rag_result(result)
        update_and_flush_trace(langfuse_client, client_type)
        # context stays empty until the MCP server has a tool for video links
        return {"question": question, "context": [], "answer": answer}
    except Exception as e:
        logger.error("MCP query failed (%s): %s", type(e).__name__, e)
        return {
            "question": question,
            "context": [],
            "answer": settings.error_messages["DefaultError"],
        }
