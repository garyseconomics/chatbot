"""Ask all test questions and store the answers in the analytics database.

Usage:
    python -m analytics.ask_all_questions
"""

import asyncio
import logging
import sqlite3
from datetime import datetime, timezone

from analytics.config import settings
from rag.rag_manager import RAG_query
from analytics.questions_for_testing import questions

logger = logging.getLogger(__name__)


async def ask_all_questions() -> None:
    conn = sqlite3.connect(settings.analytics_db_path)
    cursor = conn.cursor()

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

            timestamp = datetime.now(timezone.utc).isoformat()
            prompt_version = str(settings.prompt_version)

            cursor.execute(
                "INSERT INTO qa_test_results"
                " (timestamp, issue_category, question, answer, chat_model, prompt_version)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (timestamp, category, question, answer, settings.chat_model, prompt_version),
            )
            conn.commit()

            logger.info("Answer: %s", answer[:100])

    cursor.close()
    conn.close()
    logger.info("Done. %d questions answered and stored.", total)


if __name__ == "__main__":
    asyncio.run(ask_all_questions())
