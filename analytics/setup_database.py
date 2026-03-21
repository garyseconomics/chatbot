"""One-time setup: creates the SQLite database and user_traces table."""

import logging
import sqlite3

from config import settings

logger = logging.getLogger(__name__)


def setup_database() -> None:
    """Create the SQLite database file and user_traces table."""
    conn = sqlite3.connect(settings.analytics_db_path)
    cursor = conn.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS user_traces ("
        "  trace_id TEXT PRIMARY KEY,"
        "  user_id TEXT,"
        "  question TEXT,"
        "  answer TEXT,"
        "  timestamp TEXT,"
        "  model TEXT,"
        "  latency REAL,"
        "  prompt_version TEXT"
        ")"
    )

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS qa_test_results ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  timestamp TEXT,"
        "  issue_category TEXT,"
        "  question TEXT,"
        "  answer TEXT,"
        "  chat_model TEXT,"
        "  prompt_version TEXT"
        ")"
    )

    conn.commit()
    cursor.close()
    conn.close()

    logger.info("SQLite database ready at %s", settings.analytics_db_path)


if __name__ == "__main__":
    setup_database()
    print("Database setup complete.")