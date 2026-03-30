"""Import traces from Langfuse JSON export into SQLite database.

Handles the new Langfuse format (from 2026-03-28 onwards) where each trace
contains the full pipeline: question, answer, vector search context, and
metadata for both chat and embedding models.
"""

import json
import logging
import sqlite3
from pathlib import Path

from analytics.config import settings

logger = logging.getLogger(__name__)


# Prompt version based on deployment timestamps.
# v4 is the only version in the new format, but keeping the logic
# in case we deploy v5+ later.
def _prompt_version(timestamp: str) -> str:
    if timestamp < "2026-03-28 17:50":
        return "4"  # shouldn't happen with the new export, but just in case
    return "4"


def _parse_trace(trace: dict) -> dict | None:
    """Parse a new-format trace into a flat dict.

    New format has:
      input:  {"args": ["question"], "kwargs": {"user_id": "..."}}
      output: {"question": "...", "answer": "...", "context": [...]}
      metadata: {"chat_model": "...", "chat_provider": "...", ...}

    Returns None if the trace doesn't match this format or has an
    unrecognised user_id.
    """
    # Only import traces from known user types
    user_id = trace.get("userId")
    if not user_id:
        return None
    is_known_user = (
        user_id.startswith("discord:")
        or user_id.startswith("telegram:")
        or user_id.startswith("benchmark_")
        or user_id in ("qa_test", "cli")
    )
    if not is_known_user:
        return None

    raw_input = trace.get("input")
    if not isinstance(raw_input, dict) or "args" not in raw_input:
        return None

    args = raw_input["args"]
    if not args or not isinstance(args[0], str):
        return None

    question = args[0]
    output = trace.get("output") or {}
    answer = output.get("answer") if isinstance(output, dict) else None
    metadata = trace.get("metadata") or {}

    # Count documents returned by vector search
    context = output.get("context", []) if isinstance(output, dict) else []
    num_results = len(context)

    timestamp = trace.get("timestamp", "")

    return {
        "trace_id": trace.get("id"),
        "timestamp": timestamp,
        "user_id": trace.get("userId"),
        "question": question,
        "answer": answer,
        "prompt_version": _prompt_version(timestamp),
        "chat_model": metadata.get("chat_model"),
        "chat_provider": metadata.get("chat_provider"),
        "embedding_model": metadata.get("embedding_model"),
        "embedding_provider": metadata.get("embedding_provider"),
        "latency": trace.get("latency"),
        "num_results": num_results,
        # embedding_latency and chat_latency require fetching observations
        # from the Langfuse API separately — left NULL for now.
        "context": context,
    }


def import_traces(file_path: Path, db_path: str = None) -> None:
    """Read traces from a JSON file and insert new ones into SQLite."""
    if db_path is None:
        db_path = settings.analytics_db_path

    with open(file_path) as f:
        traces = json.load(f)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        inserted = 0
        skipped = 0
        ignored = 0
        docs_inserted = 0

        for trace in traces:
            parsed = _parse_trace(trace)
            if parsed is None:
                ignored += 1
                continue

            cursor.execute(
                "SELECT COUNT(*) FROM traces WHERE trace_id = ?",
                (parsed["trace_id"],),
            )
            if cursor.fetchone()[0] > 0:
                skipped += 1
                continue

            cursor.execute(
                "INSERT INTO traces "
                "(trace_id, timestamp, user_id, question, answer, prompt_version,"
                " chat_model, chat_provider, embedding_model, embedding_provider,"
                " latency, num_results) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    parsed["trace_id"],
                    parsed["timestamp"],
                    parsed["user_id"],
                    parsed["question"],
                    parsed["answer"],
                    parsed["prompt_version"],
                    parsed["chat_model"],
                    parsed["chat_provider"],
                    parsed["embedding_model"],
                    parsed["embedding_provider"],
                    parsed["latency"],
                    parsed["num_results"],
                ),
            )

            # Insert document references from the vector search context
            for doc in parsed["context"]:
                doc_id = doc.get("id")
                if doc_id:
                    cursor.execute(
                        "INSERT OR IGNORE INTO search_result_documents "
                        "(trace_id, document_id) VALUES (?, ?)",
                        (parsed["trace_id"], doc_id),
                    )
                    docs_inserted += 1

            inserted += 1

        conn.commit()
    finally:
        conn.close()

    logger.info(
        "Imported %d traces (%d docs), skipped %d existing, "
        "ignored %d non-matching (from %s)",
        inserted,
        docs_inserted,
        skipped,
        ignored,
        file_path.name,
    )


def find_newest_traces_file(directory: Path) -> Path | None:
    """Find the most recently modified traces JSON file in the directory."""
    files = sorted(directory.glob("traces_*.json"), key=lambda f: f.stat().st_mtime)
    if not files:
        return None
    return files[-1]


if __name__ == "__main__":
    raw_data_dir = Path(__file__).parent.parent / "raw_data"
    newest_file = find_newest_traces_file(raw_data_dir)

    if newest_file is None:
        print("No trace files found in", raw_data_dir)
    else:
        print(f"Importing from {newest_file.name}...")
        import_traces(newest_file)
        print("Done.")
