"""Import user traces from JSON files into SQLite database."""

import json
import logging
import sqlite3
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)


def find_newest_user_traces_file(directory: Path) -> Path | None:
    """Find the most recently modified user_traces JSON file in the directory."""
    files = sorted(directory.glob("user_traces_*.json"), key=lambda f: f.stat().st_mtime)
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

        for trace in traces:
            if trace_exists(cursor, trace["trace_id"]):
                skipped += 1
                continue

            cursor.execute(
                "INSERT INTO user_traces "
                "(trace_id, user_id, question, answer, timestamp, model, latency, prompt_version) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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