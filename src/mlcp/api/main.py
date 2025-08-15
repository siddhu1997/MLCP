from __future__ import annotations

from fastapi import FastAPI
from starlette import status

from mlcp.common.logger import get_logger

from .routes import runs_router


_LOG = get_logger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(title="MLCP API", version="0.0.1")

    app.include_router(runs_router)

    @app.get("/health", status_code=status.HTTP_200_OK)
    def health() -> dict[str, str]:                     # type: ignore[unused-function]
        _LOG.info("health_check")
        return {"status": "ok"}

    return app

# For `uvicorn mlcp.api.main:app --reload`
app = create_app()
