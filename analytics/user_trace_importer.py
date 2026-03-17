"""Import user traces from JSON files into MySQL database."""

import json
import logging
from pathlib import Path

import mysql.connector
from mysql.connector import errorcode

from config import settings

logger = logging.getLogger(__name__)

# Error codes for missing database (1049) and missing table (1146)
_MISSING_DB_OR_TABLE = (errorcode.ER_BAD_DB_ERROR, errorcode.ER_NO_SUCH_TABLE)


class DatabaseNotFoundError(Exception):
    """Raised when the MySQL database or table does not exist."""


def find_newest_user_traces_file(directory: Path) -> Path | None:
    """Find the most recently modified user_traces JSON file in the directory."""
    files = sorted(directory.glob("user_traces_*.json"), key=lambda f: f.stat().st_mtime)
    if not files:
        return None
    return files[-1]


def trace_exists(cursor, trace_id: str) -> bool:
    """Check if a trace_id already exists in the user_traces table."""
    cursor.execute(
        "SELECT COUNT(*) FROM user_traces WHERE trace_id = %s",
        (trace_id,),
    )
    return cursor.fetchone()[0] > 0


def import_traces(file_path: Path) -> None:
    """Read traces from a JSON file and insert new ones into MySQL."""
    with open(file_path) as f:
        traces = json.load(f)

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
            raise DatabaseNotFoundError(
                "Database not found. Run setup_database.py first:\n"
                "  python -m analytics.setup_database"
            ) from err
        raise

    cursor = conn.cursor()

    try:
        inserted = 0
        skipped = 0

        for trace in traces:
            if trace_exists(cursor, trace["trace_id"]):
                skipped += 1
                continue

            cursor.execute(
                "INSERT INTO user_traces "
                "(trace_id, user_id, question, answer, timestamp, model, latency, prompt_version) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    trace["trace_id"],
                    trace["user_id"],
                    trace["question"],
                    trace["answer"],
                    trace["timestamp"],
                    trace["model"],
                    trace["latency"],
                    "2",
                ),
            )
            inserted += 1

        conn.commit()
    except mysql.connector.Error as err:
        if err.errno in _MISSING_DB_OR_TABLE:
            raise DatabaseNotFoundError(
                "Table not found. Run setup_database.py first:\n"
                "  python -m analytics.setup_database"
            ) from err
        raise
    finally:
        conn.close()

    logger.info(
        "Imported %d new traces, skipped %d existing (from %s)",
        inserted,
        skipped,
        file_path.name,
    )


if __name__ == "__main__":
    raw_data_dir = Path(__file__).parent / "raw_data"
    newest_file = find_newest_user_traces_file(raw_data_dir)

    if newest_file is None:
        print("No user traces files found in", raw_data_dir)
    else:
        print(f"Importing from {newest_file.name}...")
        import_traces(newest_file)
        print("Done.")
