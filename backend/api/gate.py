from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.app.database import get_connection
from backend.engine.decision_engine import DecisionEngine
from backend.models.gate import (
    GateRequest,
    GateDecision,
    insert_gate_request,
    insert_gate_decision,
    insert_audit_entry,
)
from backend.audit.trail import create_audit_entry


router = APIRouter()
_engine = DecisionEngine()


class GateRequestBody(BaseModel):
    action: str
    params: dict = Field(default_factory=dict)
    context: str = ""
    session_id: str = ""


@router.post("/gate")
async def gate(body: GateRequestBody):
    result = _engine.evaluate(
        action=body.action,
        params=body.params,
        context=body.context,
    )

    conn = get_connection()
    try:
        req = GateRequest(
            action=body.action,
            session_id=body.session_id or None,
            params=body.params,
            context=body.context,
        )
        insert_gate_request(conn, req)

        decision = GateDecision(
            decision=result.decision,
            confidence=result.confidence,
            blast_radius=result.blast_radius,
            reversible=result.reversible,
            injection_detected=result.injection_detected,
            reason=result.reason,
            request_id=req.id,
            layer_results=result.to_dict()["layer_results"],
        )
        insert_gate_decision(conn, decision)

        audit = create_audit_entry(req, decision)
        insert_audit_entry(conn, audit)
    finally:
        conn.close()

    response = result.to_dict()
    response["request_id"] = req.id
    response["decision_id"] = decision.id
    response["audit_id"] = audit.id
    return response
