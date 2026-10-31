import asyncio
import logging

from config import settings
from mcp_client.mcp_manager import MCP_query
from rag.video_links import get_video_link, videos_text_for_chat

logger = logging.getLogger(__name__)


def main() -> None:
    print(settings.bot_greeting)
    question = input("Your question: ")
    # asyncio.run() needed because main() is sync but MCP_query is async
    response = asyncio.run(MCP_query(question, client_type="cli"))
    logger.debug("Full RAG response: %s", response)
    print(response["answer"])
    video_links = get_video_link(response["context"])
    video_text = videos_text_for_chat(video_links)
    if video_text:
        print(video_text)


if __name__ == "__main__":
    main()
