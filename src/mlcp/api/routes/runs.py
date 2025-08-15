from __future__ import annotations

import os
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, cast
from sqlite3 import Connection

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..db import connect
from ..models import RunCreate, RunRecord
from ..repo import create_run
from ..plan_normalize import normalize_plan
from ..plan_store import persist_plan
from ..plan_validate import JSONDict, validate_plan

router = APIRouter(prefix="/v1/runs", tags=["runs"])

class PlanSealBody(BaseModel):
    plan: Optional[dict[str, Any]] = Field(default=None, description="JSON plan object")
    plan_text: Optional[str] = Field(default=None, description="YAML or JSON as text")


class PlanSealResponse(BaseModel):
    ok: bool = True
    run_id: str
    plan_version: int
    plan_hash: str
    nodes: int
    edges: int

class PlanVersionItem(BaseModel):
    version: int
    plan_hash: str
    created_at: str

class FrontierItem(BaseModel):
    node_id: str
    role: str
    retries: int
    timeout_ms: int
    gates: list[str]

class TaskUpdateResponse(BaseModel):
    ok: bool = True
    run_id: str
    plan_version: int
    node_id: str
    status: str
    updated_at: str

@dataclass(frozen=True, slots=True)
class _NodeMeta:
    role: str
    retries: int
    timeout_ms: int
    gates: list[str]

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _latest_version(run_id: str, conn: Connection) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(plan_version), 0) AS v FROM plans WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    if row is None or int(row["v"]) == 0:
        raise HTTPException(status_code=404, detail="plan_not_found")
    return int(row["v"])

def _ensure_run_exists(run_id: str) -> None:
    conn = connect()
    row = conn.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run_not_found")
    
def _ensure_node_exists(conn: Connection, run_id: str, version: int, node_id: str) -> None:
    row = conn.execute(
        "SELECT 1 FROM plan_nodes WHERE run_id = ? AND plan_version = ? AND node_id = ?",
        (run_id, version, node_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="node_not_found")

def _upsert_task_status(run_id: str, version: int, node_id: str, status_val: str) -> TaskUpdateResponse:
    conn = connect()
    ts = _utcnow()
    with conn:
        conn.execute(
            "INSERT INTO run_tasks(run_id, plan_version, node_id, status, updated_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(run_id, plan_version, node_id) DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at",
            (run_id, version, node_id, status_val, ts),
        )
    return TaskUpdateResponse(ok=True, run_id=run_id, plan_version=version, node_id=node_id, status=status_val, updated_at=ts)


@router.post("", response_model=RunRecord, status_code=status.HTTP_201_CREATED)  # type: ignore
def _create_run(body: RunCreate) -> RunRecord:  # pyright: ignore[reportUnusedFunction]
    return create_run(body)


@router.post("/{run_id}/plan:seal", response_model=PlanSealResponse)  # type: ignore[unused-function]
def plan_seal(run_id: str, body: PlanSealBody) -> PlanSealResponse:
    _ensure_run_exists(run_id)

    ok, errors, _stats = validate_plan(plan=body.plan, plan_text=body.plan_text)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[asdict(e) for e in errors],
        )

    # normalize + store
    raw_text: str | None = None
    if body.plan is not None:
        data: JSONDict = cast(JSONDict, dict(body.plan))
    else:
        assert body.plan_text is not None
        import yaml 

        loaded = yaml.safe_load(body.plan_text)  # type: ignore[no-untyped-call]
        if not isinstance(loaded, dict):
            raise HTTPException(
                status_code=422,
                detail=[{"code": "invalid_format", "detail": "root must be object"}],
            )
        # Build a typed dict[str, JSONVal] explicitly (avoids Unknown types for k/v)
        data: JSONDict = {}
        for k_obj, v in loaded.items():  # type: ignore[dict-item]
            k = k_obj if isinstance(k_obj, str) else str(k_obj)  # type: ignore[arg-type]
            data[k] = v
        raw_text = body.plan_text

    norm = normalize_plan(data)

    data_root = Path(os.getenv("DATA_ROOT", "./workspace")).resolve()
    data_root.mkdir(parents=True, exist_ok=True)

    version, phash = persist_plan(run_id=run_id, norm=norm, data_root=data_root, raw_text=raw_text)

    return PlanSealResponse(
        ok=True,
        run_id=run_id,
        plan_version=version,
        plan_hash=phash,
        nodes=norm.stats_nodes,
        edges=norm.stats_edges,
    )

@router.get("/{run_id}/plan:versions", response_model=list[PlanVersionItem])  # type: ignore[unused-function]
def list_plan_versions(run_id: str) -> list[PlanVersionItem]:
    _ensure_run_exists(run_id)
    conn = connect()
    rows = conn.execute(
        "SELECT plan_version, plan_hash, created_at FROM plans "
        "WHERE run_id = ? ORDER BY plan_version ASC",
        (run_id,),
    ).fetchall()
    out: list[PlanVersionItem] = []
    for r in rows:
        out.append(
            PlanVersionItem(
                version=int(r["plan_version"]),
                plan_hash=str(r["plan_hash"]),
                created_at=str(r["created_at"]),
            )
        )
    return out

@router.get("/{run_id}/plan:norm.json")  # type: ignore[unused-function]
def get_plan_norm_json(run_id: str, version: Optional[int] = Query(default=None)) -> Response:
    _ensure_run_exists(run_id)
    conn = connect()
    if version is None:
        row = conn.execute(
            "SELECT plan_version, body_json FROM plan_json WHERE run_id = ? "
            "ORDER BY plan_version DESC LIMIT 1",
            (run_id,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT plan_version, body_json FROM plan_json WHERE run_id = ? AND plan_version = ?",
            (run_id, version),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="plan_not_found")
    body_json = str(row["body_json"])
    return Response(content=body_json, media_type="application/json")

@router.get("/{run_id}/frontier", response_model=list[FrontierItem])  # type: ignore[unused-function]
def get_frontier(run_id: str, version: Optional[int] = Query(default=None)) -> list[FrontierItem]:
    _ensure_run_exists(run_id)

    conn = connect()
    ver = _latest_version(run_id, conn) if version is None else int(version)


    # Load node metadata with concrete types
    node_rows = conn.execute(
        "SELECT node_id, role, retries, timeout_ms, gates_json "
        "FROM plan_nodes WHERE run_id = ? AND plan_version = ?",
        (run_id, ver),
    ).fetchall()
    meta: dict[str, _NodeMeta] = {}
    for r in node_rows:
        node_id = str(r["node_id"])
        role = str(r["role"])
        retries = int(cast(int, r["retries"]))
        timeout_ms = int(cast(int, r["timeout_ms"]))
        try:
            gates_raw = json.loads(str(r["gates_json"]))
            gates_list: list[str] = [x for x in cast(list[str], gates_raw)] if isinstance(gates_raw, list) else []
        except Exception:
            gates_list = []
        meta[node_id] = _NodeMeta(role=role, retries=retries, timeout_ms=timeout_ms, gates=gates_list)

    # Build predecessor map
    pred: dict[str, set[str]] = {nid: set[str]() for nid in meta.keys()}
    edge_rows = conn.execute(
        "SELECT src, dst FROM plan_edges WHERE run_id = ? AND plan_version = ?",
        (run_id, ver),
    ).fetchall()
    for r in edge_rows:
        a = str(r["src"])
        b = str(r["dst"])
        if b not in pred:
            pred[b] = set[str]()
        if a not in pred:
            pred[a] = set[str]()
        pred[b].add(a)

    # Completed/failed
    done_rows = conn.execute(
        "SELECT node_id, status FROM run_tasks WHERE run_id = ? AND plan_version = ?",
        (run_id, ver),
    ).fetchall()
    completed: set[str] = set()
    failed: set[str] = set()
    for r in done_rows:
        nid = str(r["node_id"])
        st = str(r["status"])
        if st == "complete":
            completed.add(nid)
        elif st == "failed":
            failed.add(nid)

    # Ready = not completed/failed and all predecessors completed
    ready: list[FrontierItem] = []
    for nid, m in meta.items():
        if nid in completed or nid in failed:
            continue
        preds = pred.get(nid, set[str]())
        if all(p in completed for p in preds):
            ready.append(
                FrontierItem(
                    node_id=nid,
                    role=m.role,
                    retries=m.retries,
                    timeout_ms=m.timeout_ms,
                    gates=m.gates,
                )
            )

    # deterministic order by node_id (string)
    ready.sort(key=lambda item: item.node_id)
    return ready

@router.post("/{run_id}/tasks/{node_id}:complete", response_model=TaskUpdateResponse)  # type: ignore[unused-function]
def task_complete(run_id: str, node_id: str, version: Optional[int] = Query(default=None)) -> TaskUpdateResponse:
    _ensure_run_exists(run_id)
    conn = connect()
    ver = _latest_version(run_id, conn) if version is None else int(version)
    _ensure_node_exists(conn, run_id, ver, node_id)
    return _upsert_task_status(run_id, ver, node_id, "complete")


@router.post("/{run_id}/tasks/{node_id}:fail", response_model=TaskUpdateResponse)  # type: ignore[unused-function]
def task_fail(run_id: str, node_id: str, version: Optional[int] = Query(default=None)) -> TaskUpdateResponse:
    _ensure_run_exists(run_id)
    conn = connect()
    ver = _latest_version(run_id, conn) if version is None else int(version)
    _ensure_node_exists(conn, run_id, ver, node_id)
    return _upsert_task_status(run_id, ver, node_id, "failed")