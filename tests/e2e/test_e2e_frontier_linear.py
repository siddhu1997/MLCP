import pytest
from tests.e2e import seal_plan, frontier_ids, latest_version, last_frontier_ready_from_events, assert_same_ids

LINEAR_YAML = """\
schema_version: "1"
nodes:
  - { id: t1, name: Build }
  - { id: t2, name: Review, role: product_owner, gates: [review] }
edges:
  - [t1, t2]
"""

@pytest.mark.e2e
def test_linear_frontier_and_events(client, new_run):
    run = new_run("E2E linear")
    # Seal
    r = seal_plan(client, run, LINEAR_YAML)
    assert r.status_code == 200
    ver = r.json()["plan_version"]

    # After seal: frontier should be [t1]
    assert frontier_ids(client, run) == ["t1"]

    # Complete t1
    rc = client.post(f"/v1/runs/{run}/tasks/t1:complete")
    assert rc.status_code == 200
    assert rc.json()["status"] == "complete"

    # Parity: latest frontier_updated.ready == /frontier
    ready_ev = last_frontier_ready_from_events(client, run, version=ver)
    ready_fr = frontier_ids(client, run)
    assert_same_ids(ready_ev, ready_fr)  # both should be ["t2"]
