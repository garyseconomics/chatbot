"""CLI viewer for traces stored in SQLite."""

import sqlite3

from analytics.config import settings

_MAX_ANSWER_LENGTH = 300


def fetch_traces(db_path: str = None) -> list[tuple]:
    """Fetch all traces from the database, ordered by timestamp descending."""
    if db_path is None:
        db_path = settings.analytics_db_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT trace_id, user_id, question, answer, timestamp,"
            " chat_model, chat_provider, latency, prompt_version, num_results "
            "FROM traces ORDER BY timestamp DESC"
        )
        return cursor.fetchall()
    finally:
        conn.close()


def format_trace(row: tuple) -> str:
    """Format a single trace row for CLI display."""
    (_, user_id, question, answer, timestamp,
     chat_model, chat_provider, latency, prompt_version, num_results) = row

    truncated_answer = answer or "(no answer)"
    if len(truncated_answer) > _MAX_ANSWER_LENGTH:
        truncated_answer = truncated_answer[:_MAX_ANSWER_LENGTH] + "..."

    latency_str = f"{latency:.1f}s" if latency else "?"

    return (
        f"{'=' * 70}\n"
        f"User: {user_id}  |  Time: {timestamp}\n"
        f"Model: {chat_model} ({chat_provider})  |  Latency: {latency_str}\n"
        f"Prompt: v{prompt_version}  |  Docs: {num_results}\n"
        f"{'─' * 70}\n"
        f"Q: {question}\n"
        f"A: {truncated_answer}\n"
    )


def main() -> None:
    """Display all traces from the database."""
    rows = fetch_traces()

    if not rows:
        print("No traces found.")
        return

    print(f"\n{len(rows)} traces:\n")
    for row in rows:
        print(format_trace(row))


if __name__ == "__main__":
    main()
