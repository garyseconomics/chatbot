"""One-time setup: creates the MySQL database, tables, and analytics user."""

import logging

import mysql.connector

from config import settings

logger = logging.getLogger(__name__)


def setup_database() -> None:
    """Connect as root and create the database, user_traces table, and analytics user."""
    conn = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_root_user,
        password=settings.mysql_root_password,
    )
    cursor = conn.cursor()

    db = settings.mysql_database
    user = settings.mysql_user
    password = settings.mysql_password

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db}")
    cursor.execute(f"USE {db}")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS user_traces ("
        "  trace_id VARCHAR(255) PRIMARY KEY,"
        "  user_id VARCHAR(255),"
        "  question TEXT,"
        "  answer TEXT,"
        "  timestamp DATETIME,"
        "  model VARCHAR(100),"
        "  latency FLOAT,"
        "  prompt_version VARCHAR(50)"
        ")"
    )

    # Create the analytics user with only the permissions it needs.
    # Uses '%' (any host) because when MySQL runs in Docker, connections
    # come from the Docker bridge IP (e.g. 172.17.0.1), not 'localhost'.
    cursor.execute(f"CREATE USER IF NOT EXISTS '{user}'@'%' IDENTIFIED BY '{password}'")
    cursor.execute(f"GRANT SELECT, INSERT ON {db}.* TO '{user}'@'%'")
    cursor.execute("FLUSH PRIVILEGES")

    conn.commit()
    cursor.close()
    conn.close()

    logger.info("Database '%s' and table 'user_traces' created successfully", db)


if __name__ == "__main__":
    setup_database()
    print("Database setup complete.")
