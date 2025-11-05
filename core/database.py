import sqlite3
from pathlib import Path
from typing import Generator, Optional, Any


DB_PATH = Path(".sage/data/sage.db")


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with sane defaults."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute(query: str, params: Optional[tuple] = None) -> None:
    """Execute a write query (INSERT, UPDATE, DELETE)."""
    conn = get_connection()
    try:
        conn.execute(query, params or ())
        conn.commit()
    finally:
        conn.close()


def fetch_all(query: str, params: Optional[tuple] = None) -> list[sqlite3.Row]:
    """Execute a SELECT query and return all rows."""
    conn = get_connection()
    try:
        cur = conn.execute(query, params or ())
        return cur.fetchall()
    finally:
        conn.close()


def fetch_one(query: str, params: Optional[tuple] = None) -> Optional[sqlite3.Row]:
    """Execute a SELECT query and return the first row."""
    conn = get_connection()
    try:
        cur = conn.execute(query, params or ())
        return cur.fetchone()
    finally:
        conn.close()


def transaction() -> Generator[sqlite3.Connection, Any, None]:
    """
    Context-managed transaction for multiple operations.
    Example:
        with transaction() as conn:
            conn.execute("INSERT ...")
            conn.execute("UPDATE ...")
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
