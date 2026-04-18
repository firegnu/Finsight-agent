import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..config import settings


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    db_path = Path(settings.db_path)
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run: python scripts/seed_data.py"
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def query_all(sql: str, params: tuple = ()) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def query_one(sql: str, params: tuple = ()) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None


def execute(sql: str, params: tuple = ()) -> int:
    """Execute a write statement. Returns lastrowid."""
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid or 0
