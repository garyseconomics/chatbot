"""Tests for the CLI trace viewer."""

import sqlite3

from analytics.setup_database import setup_database
from analytics.trace_viewer import fetch_user_traces, format_trace

SAMPLE_ROW = (
    "abc123",
    "telegram:456",
    "What is inflation?",
    "Inflation is the rate at which prices rise.",
    "2026-03-17 03:46:09",
    "qwen3:32b",
    40.015,
    "2",
)


def _create_test_db(tmp_path) -> str:
    """Create a test SQLite database with the user_traces table and return its path."""
    db_path = str(tmp_path / "test.db")
    import analytics.setup_database as setup_mod
    original = setup_mod.settings.analytics_db_path
    setup_mod.settings.analytics_db_path = db_path
    setup_database()
    setup_mod.settings.analytics_db_path = original
    return db_path


# --- fetch_user_traces tests ---


# Should query the database and return all rows.
def test_fetch_user_traces_returns_rows(tmp_path):
    db_path = _create_test_db(tmp_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_traces VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        SAMPLE_ROW,
    )
    conn.commit()
    conn.close()

    rows = fetch_user_traces(db_path=db_path)

    assert len(rows) == 1
    assert rows[0] == SAMPLE_ROW


# Should return an empty list when there are no traces.
def test_fetch_user_traces_returns_empty_when_no_data(tmp_path):
    db_path = _create_test_db(tmp_path)

    rows = fetch_user_traces(db_path=db_path)

    assert rows == []


# --- format_trace tests ---


# Should format a trace row for display, showing user, time, question, and answer.
def test_format_trace_includes_key_fields():
    output = format_trace(SAMPLE_ROW)

    assert "telegram:456" in output
    assert "What is inflation?" in output
    assert "Inflation is the rate at which prices rise." in output


# Should truncate long answers.
def test_format_trace_truncates_long_answer():
    long_answer = "A" * 500
    row = (*SAMPLE_ROW[:3], long_answer, *SAMPLE_ROW[4:])

    output = format_trace(row)

    assert len(output) < len(long_answer) + 200  # some overhead for labels
    assert "..." in output