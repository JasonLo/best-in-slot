from collections.abc import Iterable

import psycopg


def fetch_users(conn: psycopg.Connection, active_only: bool = True) -> list[tuple[int, str]]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name FROM users WHERE active = %s ORDER BY id",
            (active_only,),
        )
        return list(cur.fetchall())


def create_users(conn: psycopg.Connection, rows: Iterable[tuple[str, bool]]) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO users (name, active) VALUES (%s, %s)",
            list(rows),
        )
    conn.commit()
