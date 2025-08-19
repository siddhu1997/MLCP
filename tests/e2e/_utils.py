# tests/e2e/_utils.py
from typing import Iterable

def seal_plan(client, run_id: str, plan_text: str):
    r = client.post(f"/v1/runs/{run_id}/plan:seal", json={"plan_text": plan_text})
    return r

def frontier_ids(client, run_id: str) -> list[str]:
    r = client.get(f"/v1/runs/{run_id}/frontier")
    r.raise_for_status()
    return [it["node_id"] for it in r.json()]

def latest_version(client, run_id: str) -> int:
    r = client.get(f"/v1/runs/{run_id}/plan:versions")
    r.raise_for_status()
    return r.json()[-1]["version"]

def last_frontier_ready_from_events(client, run_id: str, version: int) -> list[str]:
    # API returns newest-first; take the first matching latest version
    r = client.get(f"/v1/runs/{run_id}/events?last=100")
    r.raise_for_status()
    for ev in r.json():
        if ev.get("kind") == "frontier_updated" and (ev.get("details", {}).get("version") == version):
            return list(ev.get("details", {}).get("ready", []) or [])
    return []

def assert_same_ids(a: Iterable[str], b: Iterable[str]):
    assert sorted(a) == sorted(b), f"Mismatch: {sorted(a)} vs {sorted(b)}"
