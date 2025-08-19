# tests/conftest.py
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from mlcp.api.main import create_app

@pytest.fixture(scope="session")
def data_root(tmp_path_factory):
    """Provide DATA_ROOT for tests. If env DATA_ROOT is set, use it; otherwise create a temp dir."""
    env = os.environ.get("DATA_ROOT")
    if env:
        p = Path(env)
        p.mkdir(parents=True, exist_ok=True)
        os.environ["DATA_ROOT"] = str(p)  # ensure children see it
        # IMPORTANT: always yield (no return)
        yield str(p)
    else:
        p = tmp_path_factory.mktemp("mlcp_e2e")
        os.environ["DATA_ROOT"] = str(p)
        # tmp_path_factory handles cleanup
        yield str(p)

@pytest.fixture(scope="session")
def app(data_root):
    # data_root fixture ensures DATA_ROOT is set before app creation
    return create_app()

@pytest.fixture()
def client(app):
    return TestClient(app)

@pytest.fixture()
def new_run(client):
    """Helper to create a run and return its id."""
    def _new_run(goals="E2E test run", project="mlcp", owner="tester"):
        r = client.post("/v1/runs", json={"goals": goals, "project": project, "owner": owner})
        assert r.status_code in (200, 201), r.text
        return r.json()["run_id"]
    return _new_run
