# tests/conftest.py
import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

# If your factory is elsewhere, adjust this import:
from mlcp.api.main import create_app

@pytest.fixture(scope="session")
def data_root():
    td = tempfile.mkdtemp(prefix="mlcp_e2e_")
    os.environ["DATA_ROOT"] = td
    yield td
    shutil.rmtree(td, ignore_errors=True)

@pytest.fixture(scope="session")
def app(data_root):
    # App uses DATA_ROOT implicitly
    return create_app()

@pytest.fixture()
def client(app):
    return TestClient(app)

@pytest.fixture()
def new_run(client):
    def _new_run(goals="E2E test run", project="mlcp", owner="tester"):
        r = client.post("/v1/runs", json={"goals": goals, "project": project, "owner": owner})
        assert r.status_code in (200, 201)
        return r.json()["run_id"]
    return _new_run
