from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias, Union

import os
import yaml

# Type aliases for JSON-like values
JSONScalar: TypeAlias = Union[str, int, float, bool, None]
JSONList: TypeAlias = list['JSONVal']
JSONDict: TypeAlias = dict[str, 'JSONVal']
JSONVal: TypeAlias = Union[JSONScalar, JSONList, JSONDict]
JSONMap = JSONDict

# -------- limits from env --------
PLAN_MAX_BYTES = int(os.getenv("PLAN_MAX_BYTES", "1000000"))
PLAN_MAX_NODES = int(os.getenv("PLAN_MAX_NODES", "500"))
PLAN_MAX_EDGES = int(os.getenv("PLAN_MAX_EDGES", "1500"))

ALLOWED_ROLES: set[str] = {"developer", "product_owner", "tester"}
ALLOWED_GATES: set[str] = {"review"}


@dataclass(frozen=True, slots=True)
class ErrorItem:
    code: str
    detail: str


@dataclass(frozen=True, slots=True)
class PlanStats:
    nodes: int
    edges: int


def _coerce_to_str_object_dict_loaded(src: Any) -> JSONDict:
    """Convert a dictionary with any types into a JSONDict with string keys."""
    if not isinstance(src, dict):
        raise TypeError("Expected dict")
    
    def coerce_value(v: Any) -> JSONVal:
        if isinstance(v, dict):
            return _coerce_to_str_object_dict_loaded(v)
        elif isinstance(v, (list, tuple)):
            return [coerce_value(x) for x in v]  # type: ignore
        elif isinstance(v, (str, int, float, bool, type(None))):
            return v
        return str(v)

    return {str(k): coerce_value(v) for k, v in src.items()}  # type: ignore


def _safe_parse(
    plan: JSONDict | None,
    plan_text: str | None,
) -> tuple[JSONDict | None, list[ErrorItem]]:
    """
    Return (data, errors).
    - If JSON `plan` is provided, trust it and copy (already dict[str, object]).
    - If `plan_text` is provided, YAML safe-load with a size check and coerce keys to str.
    """
    if plan is not None:
        return dict(plan), []  # keep as dict[str, object]

    if plan_text is None:
        return None, [ErrorItem("invalid_format", "missing plan or plan_text")]

    raw = plan_text.encode("utf-8")
    if len(raw) > PLAN_MAX_BYTES:
        return None, [ErrorItem("plan_too_large", str(len(raw)))]

    try:
        loaded = yaml.safe_load(plan_text)  # type: ignore[no-untyped-call]
    except Exception as exc:  # pragma: no cover
        return None, [ErrorItem("invalid_format", f"yaml_parse_error:{exc}")]

    if not isinstance(loaded, dict):
        return None, [ErrorItem("invalid_format", "root must be an object")]

    data = _coerce_to_str_object_dict_loaded(loaded)
    return data, []


def _collect_cycles(nodes: list[str], edges: list[tuple[str, str]], limit: int = 3) -> list[list[str]]:
    graph: dict[str, list[str]] = {n: [] for n in nodes}
    for a, b in edges:
        graph.setdefault(a, []).append(b)

    visiting: set[str] = set()
    visited: set[str] = set()
    parent: dict[str, str | None] = {n: None for n in nodes}
    cycles: list[list[str]] = []

    def dfs(u: str) -> None:
        if len(cycles) >= limit:
            return
        visiting.add(u)
        for v in graph.get(u, []):
            if v in visiting:
                # reconstruct simple cycle: v .. u -> v
                path: list[str] = [v]
                cur: str | None = u
                while cur is not None and cur != v:
                    path.append(cur)
                    cur = parent.get(cur)
                path.append(v)
                path.reverse()
                if not cycles or cycles[-1] != path:
                    cycles.append(path)
            elif v not in visited:
                parent[v] = u
                dfs(v)
                if len(cycles) >= limit:
                    return
        visiting.remove(u)
        visited.add(u)

    for n in nodes:
        if n not in visited:
            dfs(n)
            if len(cycles) >= limit:
                break
    return cycles


def validate_plan(
    plan: JSONDict | None,
    plan_text: str | None,
) -> tuple[bool, list[ErrorItem], PlanStats | None]:
    """
    Validate structure, references, and acyclicity.
    Returns: (ok, errors, stats) where errors is a list and stats is None when ok=False.
    """
    data, parse_errors = _safe_parse(plan, plan_text)
    if parse_errors:
        return False, parse_errors, None
    assert data is not None

    errors: list[ErrorItem] = []

    # --- schema_version ---
    version_raw: JSONVal = data.get("schema_version", "1")
    version = str(version_raw)
    if version != "1":
        errors.append(ErrorItem("unsupported_schema_version", version))

    # --- nodes/edges containers (typed) ---
    nodes_raw: JSONVal = data.get("nodes", [])
    edges_raw: JSONVal = data.get("edges", [])

    if isinstance(nodes_raw, list):
        nodes_seq: list[JSONVal] = list(nodes_raw)
    else:
        errors.append(ErrorItem("invalid_format", "nodes must be a list"))
        nodes_seq = []

    if isinstance(edges_raw, list):
        edges_seq: list[JSONVal] = list(edges_raw)
    else:
        errors.append(ErrorItem("invalid_format", "edges must be a list"))
        edges_seq = []

    # --- validate nodes ---
    seen: set[str] = set()
    node_ids: list[str] = []

    for idx, node_any in enumerate(nodes_seq):
        if not isinstance(node_any, dict):
            errors.append(ErrorItem("invalid_format", f"nodes[{idx}] must be an object"))
            continue

        # build a typed dict[str, object] without relying on generic .get of Unknown
        node_map: JSONMap = _coerce_to_str_object_dict_loaded(node_any)

        nid = str(node_map.get("id", "")).strip()
        name = str(node_map.get("name", "")).strip()
        role = str(node_map.get("role", "developer")).strip()

        if not nid or not name:
            errors.append(ErrorItem("empty_id_or_name", nid or f"nodes[{idx}]"))
            continue
        if nid in seen:
            errors.append(ErrorItem("duplicate_node_id", nid))
            continue
        if role not in ALLOWED_ROLES:
            errors.append(ErrorItem("invalid_role", role))

        gates_val: JSONVal = node_map.get("gates", [])
        if isinstance(gates_val, list):
            gates_list: list[object] = [g for g in gates_val]
            for g_any in gates_list:
                g = str(g_any)
                if g not in ALLOWED_GATES:
                    errors.append(ErrorItem("invalid_gate", g))
        else:
            errors.append(ErrorItem("invalid_format", f"nodes[{idx}].gates must be list"))

        seen.add(nid)
        node_ids.append(nid)

    if len(node_ids) > PLAN_MAX_NODES:
        errors.append(ErrorItem("too_many_nodes", str(len(node_ids))))

    # --- validate edges ---
    edge_list: list[tuple[str, str]] = []
    for e_any in edges_seq:
        try:
            if isinstance(e_any, (list, tuple)):
                if len(e_any) != 2:
                    errors.append(ErrorItem("invalid_edge_format", str(e_any)))
                    continue
                
                # Convert elements to strings safely
                edge_items = list(e_any)  # Convert to list to handle both tuple and list
                a = str(edge_items[0]).strip()
                b = str(edge_items[1]).strip()
            else:
                errors.append(ErrorItem("invalid_edge_format", str(e_any)))
                continue
        except (IndexError, AttributeError, TypeError):
            errors.append(ErrorItem("invalid_edge_format", str(e_any)))
            continue

        if a == b:
            errors.append(ErrorItem("self_edge", a))
        if a not in seen or b not in seen:
            errors.append(ErrorItem("edge_refers_to_unknown_node", f"{a}->{b}"))
        edge_list.append((a, b))

    if len(edge_list) > PLAN_MAX_EDGES:
        errors.append(ErrorItem("too_many_edges", str(len(edge_list))))

    # --- cycles (collect up to 3) ---
    for cyc in _collect_cycles(node_ids, edge_list, limit=3):
        errors.append(ErrorItem("cycle_detected", " -> ".join(cyc)))

    if errors:
        return False, errors, None

    return True, [], PlanStats(nodes=len(node_ids), edges=len(edge_list))
