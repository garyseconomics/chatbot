"""CLI viewer for user traces stored in SQLite."""

import sqlite3

from config import settings

_MAX_ANSWER_LENGTH = 300


def fetch_user_traces(db_path: str = None) -> list[tuple]:
    """Fetch all user traces from the database, ordered by timestamp descending."""
    if db_path is None:
        db_path = settings.analytics_db_path

    conn = sqlite3.connect(db_path)
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

    truncated_answer = answer
    if len(answer) > _MAX_ANSWER_LENGTH:
        truncated_answer = answer[:_MAX_ANSWER_LENGTH] + "..."

    return (
        f"{'=' * 70}\n"
        f"User: {user_id}  |  Time: {timestamp}  |  Model: {model}\n"
        f"Latency: {latency:.1f}s  |  Prompt: v{prompt_version}\n"
        f"{'─' * 70}\n"
        f"Q: {question}\n"
        f"A: {truncated_answer}\n"
    )


def main() -> None:
    """Display all user traces from the database."""
    rows = fetch_user_traces()

    if not rows:
        print("No user traces found.")
        return

    print(f"\n{len(rows)} user traces:\n")
    for row in rows:
        print(format_trace(row))


if __name__ == "__main__":
    main()