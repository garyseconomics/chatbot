"""Tests for importing user traces from JSON into SQLite."""

import json
import os
import sqlite3

from analytics.setup_database import setup_database
from analytics.user_trace_importer import (
    find_newest_user_traces_file,
    import_traces,
    trace_exists,
)

SAMPLE_TRACE = {
    "trace_id": "abc123",
    "user_id": "telegram:456",
    "question": "What is inflation?",
    "answer": "Inflation is the rate at which prices rise.",
    "timestamp": "2026-03-17 03:46:09.740000+00:00",
    "model": "qwen3:32b",
    "latency": 40.015,
}


def _create_test_db(tmp_path) -> str:
    """Create a test SQLite database with the user_traces table and return its path."""
    db_path = str(tmp_path / "test.db")
    # Reuse setup_database by patching the settings path
    import analytics.setup_database as setup_mod
    original = setup_mod.settings.analytics_db_path
    setup_mod.settings.analytics_db_path = db_path
    setup_database()
    setup_mod.settings.analytics_db_path = original
    return db_path


# --- find_newest_user_traces_file tests ---


# Should return the most recently modified user_traces file.
def test_find_newest_file_returns_most_recent(tmp_path):
    old_file = tmp_path / "user_traces_old.json"
    new_file = tmp_path / "user_traces_new.json"
    old_file.write_text("[]")
    new_file.write_text("[]")
    # Set explicit modification times so the test doesn't depend on filesystem
    # timestamp resolution (both files created nearly simultaneously).
    os.utime(old_file, (1000, 1000))
    os.utime(new_file, (2000, 2000))

    result = find_newest_user_traces_file(tmp_path)

    assert result == new_file


# Should return None when no user_traces files exist.
def test_find_newest_file_returns_none_when_empty(tmp_path):
    result = find_newest_user_traces_file(tmp_path)

    assert result is None


# Should ignore non-user-traces files (like other_traces).
def test_find_newest_file_ignores_other_files(tmp_path):
    other_file = tmp_path / "other_traces_2026-03-17_120000.json"
    other_file.write_text("[]")

    result = find_newest_user_traces_file(tmp_path)

    assert result is None


# --- trace_exists tests ---


# Should return True when the trace_id is already in the database.
def test_trace_exists_returns_true_when_found(tmp_path):
    db_path = _create_test_db(tmp_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_traces (trace_id, user_id, question, answer, timestamp, model, latency, prompt_version) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("abc123", "user1", "q", "a", "2026-01-01", "model", 1.0, "1"),
    )
    conn.commit()

    result = trace_exists(cursor, "abc123")

    conn.close()
    assert result is True


# Should return False when the trace_id is not in the database.
def test_trace_exists_returns_false_when_not_found(tmp_path):
    db_path = _create_test_db(tmp_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    result = trace_exists(cursor, "nonexistent")

    conn.close()
    assert result is False


# --- import_traces tests ---


# Should insert traces that are not already in the database.
def test_import_traces_inserts_new_traces(tmp_path):
    db_path = _create_test_db(tmp_path)
    traces_file = tmp_path / "user_traces_2026-03-17_120000.json"
    traces_file.write_text(json.dumps([SAMPLE_TRACE]))

    import_traces(traces_file, db_path=db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_traces")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 1


# Should skip traces that already exist in the database.
def test_import_traces_skips_existing_traces(tmp_path):
    db_path = _create_test_db(tmp_path)
    traces_file = tmp_path / "user_traces_2026-03-17_120000.json"
    traces_file.write_text(json.dumps([SAMPLE_TRACE]))

    # Import twice — second time should skip
    import_traces(traces_file, db_path=db_path)
    import_traces(traces_file, db_path=db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_traces")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 1


# Should handle a mix of new and existing traces.
def test_import_traces_handles_mix_of_new_and_existing(tmp_path):
    db_path = _create_test_db(tmp_path)

    # First import: one trace
    first_file = tmp_path / "user_traces_first.json"
    first_file.write_text(json.dumps([SAMPLE_TRACE]))
    import_traces(first_file, db_path=db_path)

    # Second import: same trace + a new one
    new_trace = {**SAMPLE_TRACE, "trace_id": "new-1"}
    second_file = tmp_path / "user_traces_second.json"
    second_file.write_text(json.dumps([SAMPLE_TRACE, new_trace]))
    import_traces(second_file, db_path=db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_traces")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 2