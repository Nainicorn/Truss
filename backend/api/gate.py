from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.engine.decision_engine import DecisionEngine


router = APIRouter()
_engine = DecisionEngine()


class GateRequestBody(BaseModel):
    action: str
    params: dict = Field(default_factory=dict)
    context: str = ""
    session_id: str = ""


@router.post("/gate")
async def gate(body: GateRequestBody):
    decision = _engine.evaluate(
        action=body.action,
        params=body.params,
        context=body.context,
    )

    return decision.to_dict()
