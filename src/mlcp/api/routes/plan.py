from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from ..plan_validate import validate_plan

router = APIRouter(prefix="/v1", tags=["plan"])


class PlanValidateBody(BaseModel):
    plan: Optional[dict[str, Any]] = Field(default=None, description="JSON plan object")
    plan_text: Optional[str] = Field(default=None, description="YAML or JSON as text")


@router.post("/plan:validate", status_code=status.HTTP_200_OK)  # type: ignore[unused-function]
def plan_validate(body: PlanValidateBody) -> dict[str, Any]:
    ok, errors, stats = validate_plan(plan=body.plan, plan_text=body.plan_text)
    if not ok:
        return {"ok": False, "errors": [asdict(e) for e in errors]}
    assert stats is not None
    return {"ok": True, "nodes": stats.nodes, "edges": stats.edges}
