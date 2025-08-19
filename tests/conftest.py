# tests/conftest.py
import os, shutil, tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from mlcp.api.main import create_app

@pytest.fixture(scope="session")
def data_root():
    env = os.environ.get("DATA_ROOT")
    if env:
        Path(env).mkdir(parents=True, exist_ok=True)
        return env
    td = tempfile.mkdtemp(prefix="mlcp_e2e_")
    os.environ["DATA_ROOT"] = td
    yield td
    shutil.rmtree(td, ignore_errors=True)

@pytest.fixture(scope="session")
def app(data_root):
    return create_app()

@pytest.fixture()
def client(app):
    return TestClient(app)
