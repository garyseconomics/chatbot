"""Ask test questions via the RAG pipeline.

Answers are not stored locally — they go to Langfuse as traces and get
imported to the analytics database by trace_importer.py.

Usage:
    python -m analytics.scripts.ask_questions                # all categories
    python -m analytics.scripts.ask_questions general bot_identity  # specific categories
    python -m analytics.scripts.ask_questions --list         # list available categories
"""

import argparse
import asyncio
import logging

from rag.rag_manager import RAG_query
from analytics.scripts.questions_for_testing import questions

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask test questions via the RAG pipeline."
    )
    parser.add_argument(
        "categories",
        nargs="*",
        help="Categories to ask. If omitted, all categories are used.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available categories and exit.",
    )
    return parser.parse_args()


def select_questions(categories: list[str]) -> dict:
    """Return the subset of questions matching the given categories."""
    if not categories:
        return questions

    unknown = set(categories) - set(questions.keys())
    if unknown:
        raise SystemExit(
            f"Unknown categories: {', '.join(sorted(unknown))}.\n"
            f"Available: {', '.join(questions.keys())}"
        )

    return {cat: questions[cat] for cat in categories}


async def ask_selected_questions(selected: dict) -> None:
    # Count total questions for progress logging
    total = sum(len(q_list) for q_list in selected.values())
    current = 0

    for category, q_list in selected.items():
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
    args = parse_args()

    if args.list:
        for name, q_list in questions.items():
            print(f"  {name} ({len(q_list)} questions)")
        raise SystemExit(0)

    selected = select_questions(args.categories)
    asyncio.run(ask_selected_questions(selected))
