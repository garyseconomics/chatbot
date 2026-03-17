"""Tests for importing user traces from JSON into MySQL."""

import json
from unittest.mock import MagicMock, patch

import mysql.connector
import pytest

from analytics.user_trace_importer import (
    DatabaseNotFoundError,
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


# --- find_newest_user_traces_file tests ---


# Should return the most recently modified user_traces file.
def test_find_newest_file_returns_most_recent(tmp_path):
    old_file = tmp_path / "user_traces_2026-03-16_120000.json"
    new_file = tmp_path / "user_traces_2026-03-17_120000.json"
    old_file.write_text("[]")
    new_file.write_text("[]")

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
def test_trace_exists_returns_true_when_found():
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)

    assert trace_exists(cursor, "abc123") is True
    cursor.execute.assert_called_once()


# Should return False when the trace_id is not in the database.
def test_trace_exists_returns_false_when_not_found():
    cursor = MagicMock()
    cursor.fetchone.return_value = (0,)

    assert trace_exists(cursor, "abc123") is False


# --- import_traces tests ---


# Should insert traces that are not already in the database.
@patch("analytics.user_trace_importer.mysql.connector.connect")
def test_import_traces_inserts_new_traces(mock_connect, tmp_path):
    traces_file = tmp_path / "user_traces_2026-03-17_120000.json"
    traces_file.write_text(json.dumps([SAMPLE_TRACE]))

    conn = MagicMock()
    cursor = MagicMock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor
    # trace_exists returns False — trace is new
    cursor.fetchone.return_value = (0,)

    import_traces(traces_file)

    # Should have called execute for: exists check + insert
    assert cursor.execute.call_count == 2
    conn.commit.assert_called_once()
    conn.close.assert_called_once()


# Should skip traces that already exist in the database.
@patch("analytics.user_trace_importer.mysql.connector.connect")
def test_import_traces_skips_existing_traces(mock_connect, tmp_path):
    traces_file = tmp_path / "user_traces_2026-03-17_120000.json"
    traces_file.write_text(json.dumps([SAMPLE_TRACE]))

    conn = MagicMock()
    cursor = MagicMock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor
    # trace_exists returns True — trace already in DB
    cursor.fetchone.return_value = (1,)

    import_traces(traces_file)

    # Should have called execute only for the exists check, not for insert
    assert cursor.execute.call_count == 1
    conn.commit.assert_called_once()
    conn.close.assert_called_once()


# Should handle a mix of new and existing traces.
@patch("analytics.user_trace_importer.mysql.connector.connect")
def test_import_traces_handles_mix_of_new_and_existing(mock_connect, tmp_path):
    existing_trace = {**SAMPLE_TRACE, "trace_id": "existing-1"}
    new_trace = {**SAMPLE_TRACE, "trace_id": "new-1"}
    traces_file = tmp_path / "user_traces_2026-03-17_120000.json"
    traces_file.write_text(json.dumps([existing_trace, new_trace]))

    conn = MagicMock()
    cursor = MagicMock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor
    # First trace exists, second doesn't
    cursor.fetchone.side_effect = [(1,), (0,)]

    import_traces(traces_file)

    # 2 exists checks + 1 insert = 3
    assert cursor.execute.call_count == 3
    conn.commit.assert_called_once()


# --- error handling tests ---


# Should raise DatabaseNotFoundError when the database doesn't exist.
@patch("analytics.user_trace_importer.mysql.connector.connect")
def test_import_traces_raises_when_database_missing(mock_connect, tmp_path):
    traces_file = tmp_path / "user_traces_2026-03-17_120000.json"
    traces_file.write_text(json.dumps([SAMPLE_TRACE]))

    mock_connect.side_effect = mysql.connector.Error(
        msg="Unknown database 'garys_economics'", errno=1049
    )

    with pytest.raises(DatabaseNotFoundError, match="setup_database"):
        import_traces(traces_file)


# Should raise DatabaseNotFoundError when the table doesn't exist.
@patch("analytics.user_trace_importer.mysql.connector.connect")
def test_import_traces_raises_when_table_missing(mock_connect, tmp_path):
    traces_file = tmp_path / "user_traces_2026-03-17_120000.json"
    traces_file.write_text(json.dumps([SAMPLE_TRACE]))

    conn = MagicMock()
    cursor = MagicMock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor
    cursor.execute.side_effect = mysql.connector.Error(
        msg="Table 'user_traces' doesn't exist", errno=1146
    )

    with pytest.raises(DatabaseNotFoundError, match="setup_database"):
        import_traces(traces_file)
