from __future__ import annotations

from fastapi import FastAPI, status
from mlcp.common.boot import ensure_workspace
from mlcp.common.logger import get_logger

ensure_workspace()
log = get_logger("context")

app = FastAPI(title="Carbon Context Engine", version="0.1.0")


@app.get("/health", status_code=status.HTTP_200_OK)
def health() -> dict[str, bool | str]:
    log.debug("health ping")
    return {"ok": True, "service": "context"}
