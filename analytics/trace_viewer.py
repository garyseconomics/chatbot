"""CLI viewer for user traces stored in MySQL."""

import mysql.connector
from mysql.connector import errorcode

from config import settings

_MISSING_DB_OR_TABLE = (errorcode.ER_BAD_DB_ERROR, errorcode.ER_NO_SUCH_TABLE)

_MAX_ANSWER_LENGTH = 300


def fetch_user_traces() -> list[tuple]:
    """Fetch all user traces from the database, ordered by timestamp descending."""
    try:
        conn = mysql.connector.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=settings.mysql_database,
        )
    except mysql.connector.Error as err:
        if err.errno in _MISSING_DB_OR_TABLE:
            print(
                "Database not found. Run setup_database.py first:\n"
                "  python -m analytics.setup_database"
            )
            return []
        raise

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
