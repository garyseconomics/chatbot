"""Tests for SQLite database setup script."""

import sqlite3

from analytics.setup_database import setup_database


# Should create the user_traces table with all expected columns.
def test_setup_creates_table_with_all_columns(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("analytics.setup_database.settings.analytics_db_path", db_path)

    setup_database()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(user_traces)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()

    expected_columns = [
        "trace_id",
        "user_id",
        "question",
        "answer",
        "timestamp",
        "model",
        "latency",
        "prompt_version",
    ]
    assert columns == expected_columns


# Running setup twice should not fail (CREATE TABLE IF NOT EXISTS).
def test_setup_is_idempotent(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("analytics.setup_database.settings.analytics_db_path", db_path)

    setup_database()
    setup_database()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(user_traces)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()

    assert "trace_id" in columns