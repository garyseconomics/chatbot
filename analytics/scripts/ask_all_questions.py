"""Ask all test questions via the RAG pipeline.

Answers are not stored locally — they go to Langfuse as traces and get
imported to the analytics database by trace_importer.py.

Usage:
    python -m analytics.scripts.ask_all_questions
"""

import asyncio
import logging

from rag.rag_manager import RAG_query
from analytics.scripts.questions_for_testing import questions

logger = logging.getLogger(__name__)


async def ask_all_questions() -> None:
    # Count total questions for progress logging
    total = sum(len(q_list) for q_list in questions.values())
    current = 0

    for category, q_list in questions.items():
        for question in q_list:
            current += 1
            logger.info("[%d/%d] Asking: %s", current, total, question)

            # Retry once if the answer is empty (thinking tokens can consume
            # the entire num_predict budget, leaving content empty).
            max_retries = 2
            for attempt in range(max_retries):
                response = await RAG_query(question, user_id="qa_test")
                answer = response["answer"]
                if answer:
                    break
                logger.warning("Empty answer (attempt %d/%d), retrying...", attempt + 1, max_retries)

            logger.info("Answer: %s", answer[:100])

    logger.info("Done. %d questions asked.", total)


if __name__ == "__main__":
    asyncio.run(ask_all_questions())
