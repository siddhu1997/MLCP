import pytest
from tests.e2e import seal_plan, frontier_ids


PLAN = """\
schema_version: "1"
nodes:
  - { id: X, name: "Start", role: developer }
  - { id: Y, name: "Gated", role: product_owner, gates: [review] }
edges:
  - [X, Y]
"""

@pytest.mark.e2e
def test_fail_once_excludes_from_frontier_and_emits_event(client, new_run):
    run = new_run("E2E fail-once")
    r = seal_plan(client, run, PLAN); assert r.status_code == 200

    # initial frontier
    f = frontier_ids(client, run); assert f == ["X"]

    # fail X once
    rf = client.post(f"/v1/runs/{run}/tasks/X:fail", json={"error": "induced failure"})
    assert rf.status_code == 200
    # failed node should not be in frontier
    assert "X" not in frontier_ids(client, run)

    # event contains will_retry + retry_count
    ev = client.get(f"/v1/runs/{run}/events?last=10").json()
    tf = next((e for e in ev if e["kind"] == "task_failed"), None)
    assert tf is not None
    assert "retry_count" in tf["details"] and "will_retry" in tf["details"]

@pytest.mark.e2e
def test_plan_stats(client, new_run):
    run = new_run("E2E stats")
    r = seal_plan(client, run, PLAN); assert r.status_code == 200
    st = client.get(f"/v1/runs/{run}/plan:stats")
    assert st.status_code == 200
    body = st.json()
    assert body["nodes"] == 2
    assert body["edges"] == 1
    assert body["per_role"]["developer"] >= 1
    assert body["gated"] >= 1  # gates_json not empty
