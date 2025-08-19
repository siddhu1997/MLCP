import pytest
from tests.e2e import seal_plan

PLAN_V1 = """\
schema_version: "1"
nodes:
  - { id: A, name: "Design", role: product_owner }
  - { id: B, name: "Build",  role: developer }
  - { id: C, name: "Docs",   role: developer }
  - { id: D, name: "Test",   role: developer }
edges:
  - [A, B]
  - [A, C]
  - [B, D]
  - [C, D]
"""

PLAN_V2 = PLAN_V1.replace("Docs", "Docs v2", 1)

@pytest.mark.e2e
def test_reseal_increments_version_and_changes_hash(client, new_run):
    run = new_run("E2E reseal")
    r1 = seal_plan(client, run, PLAN_V1); assert r1.status_code == 200
    v1 = r1.json()["plan_version"]; h1 = r1.json()["plan_hash"]

    r2 = seal_plan(client, run, PLAN_V2); assert r2.status_code == 200
    v2 = r2.json()["plan_version"]; h2 = r2.json()["plan_hash"]

    assert v2 == v1 + 1
    assert h2 != h1

@pytest.mark.e2e
def test_negative_invalid_edge_and_cycle_422(client, new_run):
    # invalid edge
    run1 = new_run("neg invalid-edge")
    bad1 = """schema_version: "1"
nodes:
  - { id: A, name: "A", role: developer }
edges:
  - [A, B]"""
    r1 = seal_plan(client, run1, bad1)
    assert r1.status_code == 422

    # cycle
    run2 = new_run("neg cycle")
    bad2 = """schema_version: "1"
nodes:
  - { id: A, name: "A", role: developer }
  - { id: B, name: "B", role: developer }
edges:
  - [A, B]
  - [B, A]"""
    r2 = seal_plan(client, run2, bad2)
    assert r2.status_code == 422
