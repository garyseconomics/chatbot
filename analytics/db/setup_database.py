"""One-time setup: creates the SQLite database and tables."""

import logging
import sqlite3

from analytics.config import settings

logger = logging.getLogger(__name__)


def setup_database() -> None:
    """Create the SQLite database file and tables."""
    conn = sqlite3.connect(settings.analytics_db_path)
    cursor = conn.cursor()

    # Unified traces table. Holds both real user traces and test question
    # traces — differentiate by user_id (discord:*, telegram:*, qa_test, cli).
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS traces ("
        "  trace_id TEXT PRIMARY KEY,"
        "  timestamp TEXT,"
        "  user_id TEXT,"
        "  question TEXT,"
        "  answer TEXT,"
        "  prompt_version TEXT,"
        "  chat_model TEXT,"
        "  chat_provider TEXT,"
        "  embedding_model TEXT,"
        "  embedding_provider TEXT,"
        "  latency REAL,"
        "  num_results INTEGER,"
        "  embedding_latency REAL,"
        "  chat_latency REAL"
        ")"
    )

    # Links traces to the Chroma documents returned by vector search.
    # Each row is one document in one search result.
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS search_result_documents ("
        "  trace_id TEXT,"
        "  document_id TEXT,"
        "  PRIMARY KEY (trace_id, document_id)"
        ")"
    )

    # Backup of Chroma document content. Populated by a separate script
    # so we can look up document text even if the vector DB is rebuilt.
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS document_content ("
        "  document_id TEXT PRIMARY KEY,"
        "  source TEXT,"
        "  content TEXT"
        ")"
    )

    conn.commit()
    cursor.close()
    conn.close()

    logger.info("SQLite database ready at %s", settings.analytics_db_path)


if __name__ == "__main__":
    setup_database()
    print("Database setup complete.")