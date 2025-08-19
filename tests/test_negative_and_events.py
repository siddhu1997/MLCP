import os, tempfile
from fastapi.testclient import TestClient
from mlcp.api.main import create_app

def _client():
    td = tempfile.TemporaryDirectory()
    os.environ["DATA_ROOT"] = td.name  # isolate DB/artifacts
    return TestClient(create_app()), td

def _mk_run(c: TestClient) -> str:
    r = c.post("/v1/runs", json={"goals":"pytest","project":"mlcp","owner":"tester"})
    assert r.status_code in (200, 201)
    return r.json()["run_id"]

def test_seal_invalid_edge_and_cycle():
    c, _td = _client()
    run = _mk_run(c)

    bad1: str = """
    schema_version: "1"
        nodes:
            - {id: A, name: "A", role: developer}
        edges:
            - [A, B]
    """
    r1 = c.post(f"/v1/runs/{run}/plan:seal", json={"plan_text": bad1})
    assert r1.status_code == 422

    run2 = _mk_run(c)
    bad2 = """
    schema_version: "1"
    nodes:
        - {id: A, name: "A", role: developer}
        - {id: B, name: "B", role: developer}
    edges:
        - [A, B]
        - [B, A]
    """
    r2 = c.post(f"/v1/runs/{run2}/plan:seal", json={"plan_text": bad2})
    assert r2.status_code == 422

def test_events_smoke_and_task_completed():
    c, _td = _client()
    run = _mk_run(c)
    ok_plan = """
    schema_version: "1"
    nodes:
        - { id: A, name: "A", role: developer }
        - { id: B, name: "B", role: developer }
    edges:
        - [A, B]
    """
    r = c.post(f"/v1/runs/{run}/plan:seal", json={"plan_text": ok_plan})
    assert r.status_code == 200

    # events: should include plan_sealed and frontier_updated
    ev = c.get(f"/v1/runs/{run}/events?last=10").json()
    kinds = {e["kind"] for e in ev}
    assert "plan_sealed" in kinds
    assert "frontier_updated" in kinds

    # complete A -> expect task_completed & frontier_updated again
    f = c.get(f"/v1/runs/{run}/frontier").json()
    assert any(item["node_id"] == "A" for item in f)
    rc = c.post(f"/v1/runs/{run}/tasks/A:complete")
    assert rc.status_code == 200

    ev2 = c.get(f"/v1/runs/{run}/events?last=10").json()
    kinds2 = [e["kind"] for e in ev2]
    assert "task_completed" in kinds2
    assert "frontier_updated" in kinds2
