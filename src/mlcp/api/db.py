from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Final

from mlcp.common.logger import get_logger

_LOG = get_logger(__name__)
_DB_NAME: Final[str] = "mlcp.db"


def _db_path() -> Path:
    root = Path(os.getenv("DATA_ROOT", "./workspace")) / "db"
    root.mkdir(parents=True, exist_ok=True)
    return root / _DB_NAME


def connect() -> sqlite3.Connection:
    """Open a SQLite connection in WAL mode with safe defaults and ensure schema."""
    path = _db_path()
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")

        # existing runs table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
              run_id      TEXT PRIMARY KEY,
              state       TEXT NOT NULL,
              goals       TEXT NOT NULL,
              project     TEXT NOT NULL,
              owner       TEXT NOT NULL,
              plan_sealed INTEGER NOT NULL DEFAULT 0,
              created_at  TEXT NOT NULL,
              updated_at  TEXT NOT NULL
            )
            """
        )

        # plan metadata (versioned per run)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plans (
              run_id       TEXT NOT NULL,
              plan_version INTEGER NOT NULL,
              plan_hash    TEXT NOT NULL,
              created_at   TEXT NOT NULL,
              PRIMARY KEY (run_id, plan_version),
              FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
            )
            """
        )

        # normalized plan JSON blob (authoritative runtime form)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plan_json (
              run_id       TEXT NOT NULL,
              plan_version INTEGER NOT NULL,
              body_json    TEXT NOT NULL,
              FOREIGN KEY (run_id, plan_version) REFERENCES plans(run_id, plan_version) ON DELETE CASCADE
            )
            """
        )

        # per-node index (fast lookups by task id)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plan_nodes (
              run_id       TEXT NOT NULL,
              plan_version INTEGER NOT NULL,
              node_id      TEXT NOT NULL,
              role         TEXT NOT NULL,
              retries      INTEGER NOT NULL,
              timeout_ms   INTEGER NOT NULL,
              gates_json   TEXT NOT NULL,
              PRIMARY KEY (run_id, plan_version, node_id),
              FOREIGN KEY (run_id, plan_version) REFERENCES plans(run_id, plan_version) ON DELETE CASCADE
            )
            """
        )

        # edges index (fast fan-out queries)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plan_edges (
              run_id       TEXT NOT NULL,
              plan_version INTEGER NOT NULL,
              src          TEXT NOT NULL,
              dst          TEXT NOT NULL,
              FOREIGN KEY (run_id, plan_version)
                REFERENCES plans(run_id, plan_version)
                ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_plan_edges_frontier "
            "ON plan_edges(run_id, plan_version, src)"
        )

        # task states per run & plan version
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_tasks (
              run_id       TEXT NOT NULL,
              plan_version INTEGER NOT NULL,
              node_id      TEXT NOT NULL,
              status       TEXT NOT NULL,  -- pending|complete|failed
              updated_at   TEXT NOT NULL,
              PRIMARY KEY (run_id, plan_version, node_id),
              FOREIGN KEY (run_id, plan_version)
                REFERENCES plans(run_id, plan_version)
                ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_run_tasks_status "
            "ON run_tasks(run_id, plan_version, status)"
        )

    _LOG.info("db_ready", path=str(path))
    return conn
