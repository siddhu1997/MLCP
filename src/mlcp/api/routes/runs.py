from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..models import RunCreate, RunRecord, SealBody
from ..repo import create_run, seal_plan

router = APIRouter(prefix="/v1/runs", tags=["runs"])


@router.post("", response_model=RunRecord, status_code=status.HTTP_201_CREATED)  # type: ignore
def _create_run(body: RunCreate) -> RunRecord: # pyright: ignore[reportUnusedFunction]
    return create_run(body)


@router.post("/{run_id}/plan:seal", response_model=RunRecord)  # type: ignore
def _seal_plan(run_id: str, _body: SealBody) -> RunRecord: # pyright: ignore[reportUnusedFunction]
    rec = seal_plan(run_id)
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run_not_found")
    return rec
