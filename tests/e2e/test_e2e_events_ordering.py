import json
import pytest
from mlcp.api.db import connect
from fastapi.testclient import TestClient

@pytest.mark.e2e
def test_events_order_ties_id_desc(client, new_run):
    # Create run
    run_id = new_run("E2E event order tie-breaker")

    # Insert two events with the SAME timestamp
    conn = connect()
    ts = "2025-08-19T10:00:00+00:00"
    with conn:
        conn.execute("INSERT INTO run_events(run_id, ts, kind, details) VALUES(?,?,?,?)",
                     (run_id, ts, "frontier_updated", json.dumps({"version": 1, "ready": ["t1"]})))
        conn.execute("INSERT INTO run_events(run_id, ts, kind, details) VALUES(?,?,?,?)",
                     (run_id, ts, "frontier_updated", json.dumps({"version": 1, "ready": ["t2"]})))

    # Newest-first with tie-breaker should surface the 2nd insert first
    ev = client.get(f"/v1/runs/{run_id}/events?last=5").json()
    first_fu = next(e for e in ev if e["kind"] == "frontier_updated")
    assert first_fu["details"]["ready"] == ["t2"]
