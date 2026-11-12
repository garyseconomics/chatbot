import asyncio
import logging

from langchain_core.messages import HumanMessage

from config import settings
from orchestrator.orchestrator import answer_question

logger = logging.getLogger(__name__)


async def main() -> None:
    print(settings.bot_greeting)
    # The conversation so far and the knowledge retrieved, kept while the CLI runs
    conversation = []
    knowledge = {}
    while True:
        question = input("Your question (or 'quit' to exit): ")
        if question.strip().lower() == "quit":
            break
        conversation.append(HumanMessage(content=question))
        answer = await answer_question(conversation, knowledge, client_type="cli")
        print(answer)


if __name__ == "__main__":
    # asyncio.run() needed because main() is async (answer_question is async)
    asyncio.run(main())
