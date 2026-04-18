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
