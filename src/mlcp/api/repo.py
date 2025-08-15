from __future__ import annotations

import time
import uuid
from typing import Optional

from .db import connect
from .models import RunCreate, RunRecord, utcnow


def _mk_run_id() -> str:
    """Generate a run ID with timestamp + short UUID for ordering & uniqueness."""
    ts = int(time.time())
    return f"run_{ts}_{uuid.uuid4().hex[:8]}"


def create_run(payload: RunCreate) -> RunRecord:
    conn = connect()
    run_id = _mk_run_id()
    now = utcnow()
    with conn:
        conn.execute(
            """
            INSERT INTO runs(run_id, state, goals, project, owner, plan_sealed, created_at, updated_at)
            VALUES (?, 'INITIALISED', ?, ?, ?, 0, ?, ?)
            """,
            (run_id, payload.goals, payload.project, payload.owner, now, now),
        )
        row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    assert row is not None
    return RunRecord(**dict(row))


def seal_plan(run_id: str) -> Optional[RunRecord]:
    conn = connect()
    with conn:
        row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE runs SET plan_sealed = 1, state = 'AWAITING_EXECUTION', updated_at = ? WHERE run_id = ?",
            (utcnow(), run_id),
        )
        row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    assert row is not None
    return RunRecord(**dict(row))
