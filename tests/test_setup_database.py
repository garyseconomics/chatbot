"""Tests for MySQL database setup script."""

from unittest.mock import MagicMock, patch

from analytics.setup_database import setup_database


# Should create the database, user_traces table, and analytics user.
@patch("analytics.setup_database.mysql.connector.connect")
def test_setup_creates_database_table_and_user(mock_connect):
    conn = MagicMock()
    cursor = MagicMock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    setup_database()

    # Check that it connected with root credentials
    connect_kwargs = mock_connect.call_args[1]
    assert connect_kwargs["user"] != ""

    # Should have executed SQL for: create DB, use DB, create table, create user, grant
    executed_sql = [c[0][0] for c in cursor.execute.call_args_list]
    assert any("CREATE DATABASE" in sql for sql in executed_sql)
    assert any("CREATE TABLE" in sql for sql in executed_sql)
    assert any("user_traces" in sql for sql in executed_sql)
    assert any("prompt_version" in sql for sql in executed_sql)

    conn.commit.assert_called()
    cursor.close.assert_called_once()
    conn.close.assert_called_once()


# The table should include all expected columns.
@patch("analytics.setup_database.mysql.connector.connect")
def test_setup_table_has_all_columns(mock_connect):
    conn = MagicMock()
    cursor = MagicMock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    setup_database()

    executed_sql = " ".join(c[0][0] for c in cursor.execute.call_args_list)
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
    for col in expected_columns:
        assert col in executed_sql, f"Missing column: {col}"
