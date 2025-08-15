from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

from .db import connect
from .plan_normalize import PlanNorm, plan_hash

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _next_version(run_id: str) -> int:
    conn = connect()
    row = conn.execute(
        "SELECT COALESCE(MAX(plan_version), 0) AS v FROM plans WHERE run_id = ?", (run_id,)
    ).fetchone()
    assert row is not None
    return int(row["v"]) + 1


def persist_plan(run_id: str, norm: PlanNorm, data_root: Path, raw_text: str | None) -> Tuple[int, str]:
    """
    Stores the normalized plan and indexes. Returns (plan_version, plan_hash).
    Optionally writes the raw upload to workspace for audit.
    """
    version = _next_version(run_id)
    phash = plan_hash(norm)
    conn = connect()

    body_json = json.dumps(asdict(norm), separators=(",", ":"))
    now = _utcnow()

    nodes_rows = [
        (
            run_id,
            version,
            n.id,
            n.role,
            int(n.retries),
            int(n.timeout_ms),
            json.dumps(n.gates, separators=(",", ":")),
        )
        for n in norm.nodes
    ]
    edges_rows = [(run_id, version, a, b) for (a, b) in norm.edges]

    with conn:
        conn.execute(
            "INSERT INTO plans(run_id, plan_version, plan_hash, created_at) VALUES (?, ?, ?, ?)",
            (run_id, version, phash, now),
        )
        conn.execute(
            "INSERT INTO plan_json(run_id, plan_version, body_json) VALUES (?, ?, ?)",
            (run_id, version, body_json),
        )
        conn.executemany(
            "INSERT INTO plan_nodes(run_id, plan_version, node_id, role, retries, timeout_ms, gates_json)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            nodes_rows,
        )
        if edges_rows:
             conn.executemany(
                "INSERT INTO plan_edges(run_id, plan_version, src, dst) VALUES (?, ?, ?, ?)",
                edges_rows,
            )
        # flip run state
        conn.execute(
            "UPDATE runs SET plan_sealed = 1, state = 'AWAITING_EXECUTION', updated_at = ? WHERE run_id = ?",
            (now, run_id),
        )

    # optional audit artifact
    plan_dir = data_root / "layers" / "plans" / run_id
    plan_dir = data_root / "layers" / "plans" / run_id
    plan_dir.mkdir(parents=True, exist_ok=True)

    if raw_text is not None:
        # The user uploaded text (YAML or JSON string). Preserve as YAML artifact.
        artifact = plan_dir / f"v{version}.yaml"
        artifact.write_text(raw_text, encoding="utf-8")
    else:
        # We received structured JSON -> persist the normalized JSON artifact.
        artifact = plan_dir / f"v{version}.json"
        artifact.write_text(body_json, encoding="utf-8")

    return version, phash