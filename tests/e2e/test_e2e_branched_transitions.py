import pytest
from tests.e2e import seal_plan, frontier_ids, latest_version, last_frontier_ready_from_events, assert_same_ids

PLAN = """\
schema_version: "1"
nodes:
  - { id: A, name: "Design", role: product_owner }
  - { id: B, name: "Build",  role: developer }
  - { id: C, name: "Docs",   role: developer }
  - { id: D, name: "Test",   role: tester }
edges:
  - [A, B]
  - [A, C]
  - [B, D]
  - [C, D]
"""

@pytest.mark.e2e
def test_branched_frontier_transitions(client, new_run):
    run = new_run("E2E branched")
    r = seal_plan(client, run, PLAN)
    assert r.status_code == 200
    ver = r.json()["plan_version"]

    # [A]
    assert frontier_ids(client, run) == ["A"]

    # complete A → [B, C]
    assert client.post(f"/v1/runs/{run}/tasks/A:complete").status_code == 200
    assert_same_ids(frontier_ids(client, run), ["B", "C"])
    assert_same_ids(last_frontier_ready_from_events(client, run, ver), ["B", "C"])

    # complete B → [C]
    assert client.post(f"/v1/runs/{run}/tasks/B:complete").status_code == 200
    assert frontier_ids(client, run) == ["C"]

    # complete C → [D]
    assert client.post(f"/v1/runs/{run}/tasks/C:complete").status_code == 200
    assert frontier_ids(client, run) == ["D"]
