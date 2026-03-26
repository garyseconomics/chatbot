"""Import user traces from JSON files into SQLite database."""

import json
import logging
import sqlite3
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)


def find_newest_traces_file(directory: Path) -> Path | None:
    """Find the most recently modified traces JSON file in the directory.

    Looks for user_traces_*.json first (old export format),
    then traces_*.json (new raw export format).
    """
    files = sorted(directory.glob("user_traces_*.json"), key=lambda f: f.stat().st_mtime)
    if not files:
        files = sorted(directory.glob("traces_*.json"), key=lambda f: f.stat().st_mtime)
    if not files:
        return None
    return files[-1]


def trace_exists(cursor, trace_id: str) -> bool:
    """Check if a trace_id already exists in the user_traces table."""
    cursor.execute(
        "SELECT COUNT(*) FROM user_traces WHERE trace_id = ?",
        (trace_id,),
    )
    return cursor.fetchone()[0] > 0


# Tries to extract the user's question from the structured input.
# User traces have the question embedded in a prompt like:
#   "Question: <the actual question>\nReference material: ..."
# Returns None if the input doesn't match this format.
def _extract_question(raw_input) -> str | None:
    if not isinstance(raw_input, dict) or "args" not in raw_input:
        return None
    try:
        content = raw_input["args"][0]["messages"][0]["content"]
        if "Question: " not in content:
            return None
        return content.split("Question: ", 1)[1].split("\nReference material:")[0]
    except (KeyError, IndexError, TypeError):
        return None


# Tries to extract the answer text from the structured output.
# Returns None if the output doesn't match this format.
def _extract_answer(raw_output) -> str | None:
    if isinstance(raw_output, dict) and "content" in raw_output:
        return raw_output["content"]
    return None


def _parse_user_trace(trace: dict) -> dict | None:
    """Parse a trace into a flat dict with question and answer.

    Supports two formats:
    - Flat format (old user_traces_*.json): question, answer, trace_id, etc.
    - Raw export format (new traces_*.json): id, input, output, metadata.
    Returns None if the trace is not a user trace.
    """
    # Flat format: fields already extracted
    if "question" in trace and "answer" in trace:
        return {
            "trace_id": trace["trace_id"],
            "user_id": trace.get("user_id"),
            "question": trace["question"],
            "answer": trace["answer"],
            "timestamp": trace.get("timestamp"),
            "model": trace.get("model", "unknown"),
            "latency": trace.get("latency"),
        }

    # Raw export format
    raw_input = trace.get("input")
    question = _extract_question(raw_input)
    if question is None:
        return None

    answer = _extract_answer(trace.get("output"))
    metadata = trace.get("metadata") or {}

    return {
        "trace_id": trace.get("id"),
        "user_id": trace.get("user_id") or trace.get("userId"),
        "question": question,
        "answer": answer,
        "timestamp": trace.get("timestamp"),
        "model": metadata.get("model", "unknown"),
        "latency": trace.get("latency"),
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
        not_user_trace = 0

        for trace in traces:
            parsed = _parse_user_trace(trace)
            if parsed is None:
                not_user_trace += 1
                continue

            if trace_exists(cursor, parsed["trace_id"]):
                skipped += 1
                continue

            cursor.execute(
                "INSERT INTO user_traces "
                "(trace_id, user_id, question, answer, timestamp, model, latency, prompt_version) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    parsed["trace_id"],
                    parsed["user_id"],
                    parsed["question"],
                    parsed["answer"],
                    parsed["timestamp"],
                    parsed["model"],
                    parsed["latency"],
                    "2",
                ),
            )
            inserted += 1

        conn.commit()
    finally:
        conn.close()

    logger.info(
        "Imported %d new traces, skipped %d existing, "
        "ignored %d non-user traces (from %s)",
        inserted,
        skipped,
        not_user_trace,
        file_path.name,
    )


if __name__ == "__main__":
    raw_data_dir = Path(__file__).parent / "raw_data"
    newest_file = find_newest_traces_file(raw_data_dir)

    if newest_file is None:
        print("No trace files found in", raw_data_dir)
    else:
        print(f"Importing from {newest_file.name}...")
        import_traces(newest_file)
        print("Done.")