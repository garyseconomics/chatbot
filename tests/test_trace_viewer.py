"""Tests for the CLI trace viewer."""

from unittest.mock import MagicMock, patch

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


# --- fetch_user_traces tests ---


# Should query the database and return all rows.
@patch("analytics.trace_viewer.mysql.connector.connect")
def test_fetch_user_traces_returns_rows(mock_connect):
    conn = MagicMock()
    cursor = MagicMock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor
    cursor.fetchall.return_value = [SAMPLE_ROW]

    rows = fetch_user_traces()

    assert len(rows) == 1
    assert rows[0] == SAMPLE_ROW
    cursor.execute.assert_called_once()
    conn.close.assert_called_once()


# Should return an empty list when there are no traces.
@patch("analytics.trace_viewer.mysql.connector.connect")
def test_fetch_user_traces_returns_empty_when_no_data(mock_connect):
    conn = MagicMock()
    cursor = MagicMock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor
    cursor.fetchall.return_value = []

    rows = fetch_user_traces()

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
