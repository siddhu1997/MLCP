from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from mlcp.common.logger import get_logger

_LOG = get_logger(__name__)


def _db_path() -> Path:
    root = Path(os.getenv("DATA_ROOT", "/workspace")) / "db"
    root.mkdir(parents=True, exist_ok=True)
    return root / "mlcp.db"


def connect() -> sqlite3.Connection:
    """Open a SQLite connection in WAL mode with safe defaults."""
    path = _db_path()
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    with conn:  # pragma & schema once
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
              run_id     TEXT PRIMARY KEY,
              state      TEXT NOT NULL,
              goals      TEXT NOT NULL,
              project    TEXT NOT NULL,
              owner      TEXT NOT NULL,
              plan_sealed INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
    _LOG.debug("db_ready", path=str(path))
    return conn
