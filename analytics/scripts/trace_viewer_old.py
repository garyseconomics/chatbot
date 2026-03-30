"""CLI viewer for user traces in the old database (analytics_old.db).

Shows traces from before the Langfuse format change (2026-03-28).
"""

import sqlite3
from pathlib import Path

_MAX_ANSWER_LENGTH = 300
_OLD_DB_PATH = str(Path(__file__).parent.parent / "analytics_old.db")


def fetch_user_traces() -> list[tuple]:
    """Fetch all user traces from the old database, ordered by timestamp descending."""
    conn = sqlite3.connect(_OLD_DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT trace_id, user_id, question, answer, timestamp, model, latency, prompt_version "
            "FROM user_traces ORDER BY timestamp DESC"
        )
        return cursor.fetchall()
    finally:
        conn.close()


def format_trace(row: tuple) -> str:
    """Format a single trace row for CLI display."""
    _, user_id, question, answer, timestamp, model, latency, prompt_version = row

    truncated_answer = answer or "(no answer)"
    if len(truncated_answer) > _MAX_ANSWER_LENGTH:
        truncated_answer = truncated_answer[:_MAX_ANSWER_LENGTH] + "..."

    latency_str = f"{latency:.1f}s" if latency else "?"

    return (
        f"{'=' * 70}\n"
        f"User: {user_id}  |  Time: {timestamp}  |  Model: {model}\n"
        f"Latency: {latency_str}  |  Prompt: v{prompt_version}\n"
        f"{'─' * 70}\n"
        f"Q: {question}\n"
        f"A: {truncated_answer}\n"
    )


def main() -> None:
    """Display all user traces from the old database."""
    rows = fetch_user_traces()

    if not rows:
        print("No user traces found in", _OLD_DB_PATH)
        return

    print(f"\n{len(rows)} user traces (from analytics_old.db):\n")
    for row in rows:
        print(format_trace(row))


if __name__ == "__main__":
    main()
