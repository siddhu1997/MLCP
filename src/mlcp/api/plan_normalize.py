from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from hashlib import sha256
from typing import TypeAlias

from .plan_validate import JSONDict, JSONVal, ALLOWED_GATES, ALLOWED_ROLES

NodeList: TypeAlias = list[JSONDict]
EdgeList: TypeAlias = list[tuple[str, str]]


@dataclass(frozen=True, slots=True)
class NodeNorm:
    id: str
    name: str
    role: str
    retries: int
    timeout_ms: int
    gates: list[str]


@dataclass(frozen=True, slots=True)
class PlanNorm:
    schema_version: str
    nodes: list[NodeNorm]
    edges: EdgeList
    stats_nodes: int
    stats_edges: int


def _compact_space(s: str) -> str:
    return " ".join(s.split())


def _norm_int(v: JSONVal, default: int, min_value: int) -> int:
    try:
        out = int(v)  # type: ignore[arg-type]
    except Exception:
        return default
    return max(min_value, out)


def normalize_plan(data: JSONDict) -> PlanNorm:
    # nodes
    raw_nodes = data.get("nodes", [])
    nodes: list[NodeNorm] = []
    if isinstance(raw_nodes, list):
        for n in raw_nodes:
            if not isinstance(n, dict):
                continue
            nid = _compact_space(str(n.get("id", "")).strip())
            name = _compact_space(str(n.get("name", "")).strip())
            role = str(n.get("role", "developer")).strip()
            retries = _norm_int(n.get("retries", 1), default=1, min_value=0)
            timeout_ms = _norm_int(n.get("timeout_ms", 120_000), default=120_000, min_value=1_000)

            gates_in = n.get("gates", [])
            gates: list[str] = []
            if isinstance(gates_in, list):
                for g in gates_in:
                    gstr = str(g).strip()
                    if gstr in ALLOWED_GATES:
                        gates.append(gstr)
            # sanify role (validator already warned; here we just clamp)
            if role not in ALLOWED_ROLES:
                role = "developer"

            nodes.append(NodeNorm(id=nid, name=name, role=role, retries=retries, timeout_ms=timeout_ms,
                                  gates=sorted(set(gates))))

    # edges
    raw_edges = data.get("edges", [])
    edges: EdgeList = []
    if isinstance(raw_edges, list):
        for e in raw_edges:
            if isinstance(e, (list, tuple)) and len(e) == 2:
                a = str(e[0]).strip()
                b = str(e[1]).strip()
                edges.append((a, b))

    nodes_sorted = sorted(nodes, key=lambda x: x.id)
    edges_sorted = sorted(edges, key=lambda p: (p[0], p[1]))

    return PlanNorm(
        schema_version=str(data.get("schema_version", "1")),
        nodes=nodes_sorted,
        edges=edges_sorted,
        stats_nodes=len(nodes_sorted),
        stats_edges=len(edges_sorted),
    )


def plan_hash(norm: PlanNorm) -> str:
    payload = json.dumps(asdict(norm), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(payload).hexdigest()
