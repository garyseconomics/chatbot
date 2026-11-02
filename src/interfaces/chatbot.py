import asyncio
import logging

from config import settings
from mcp_client.mcp_manager import MCP_query

logger = logging.getLogger(__name__)


def main() -> None:
    print(settings.bot_greeting)
    question = input("Your question: ")
    # asyncio.run() needed because main() is sync but MCP_query is async
    response = asyncio.run(MCP_query(question, client_type="cli"))
    logger.debug("Full RAG response: %s", response)
    print(response["answer"])


if __name__ == "__main__":
    main()
