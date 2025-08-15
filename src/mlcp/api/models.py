from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RunCreate(BaseModel):
    goals: str = Field(min_length=1)
    project: str = "mlcp"
    owner: str = "operator"


class RunRecord(BaseModel):
    run_id: str
    state: str
    goals: str
    project: str
    owner: str
    plan_sealed: int
    created_at: str
    updated_at: str


class SealBody(BaseModel):
    # Placeholder for future plan payload; optional in MVP
    pass
