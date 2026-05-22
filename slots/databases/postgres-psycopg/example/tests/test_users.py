"""
Tests use sqlite via stdlib + a tiny adapter to keep the example runnable
without a real Postgres. The psycopg API is exercised separately when DATABASE_URL is set.
"""

import os
import sqlite3

import pytest


def _setup_sqlite() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, active INTEGER)")
    conn.execute("INSERT INTO users (name, active) VALUES (?, ?)", ("alice", 1))
    conn.execute("INSERT INTO users (name, active) VALUES (?, ?)", ("bob", 0))
    conn.commit()
    return conn


def test_psycopg_module_imports() -> None:
    import psycopg  # noqa: F401  - sanity check the install


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs Postgres")
def test_against_real_postgres() -> None:
    import psycopg

    from psycopg_example import create_users, fetch_users

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TEMP TABLE users (id serial PRIMARY KEY, name text, active bool)"
            )
        create_users(conn, [("alice", True), ("bob", False)])
        rows = fetch_users(conn, active_only=True)
        assert [r[1] for r in rows] == ["alice"]
