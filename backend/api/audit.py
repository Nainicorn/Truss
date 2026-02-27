from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.app.database import get_connection
from backend.models.gate import (
    AuditEntry,
    GateRequest,
    GateDecision,
    get_audit_entry,
    get_gate_request,
    get_gate_decision,
)
from backend.audit.trail import verify


router = APIRouter()


@router.get("/audit")
async def list_audit(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session_id: str = Query(default=""),
):
    conn = get_connection()
    try:
        if session_id:
            rows = conn.execute(
                "SELECT ae.* FROM audit_entries ae "
                "JOIN gate_requests gr ON ae.request_id = gr.id "
                "WHERE gr.session_id = ? "
                "ORDER BY ae.created_at DESC LIMIT ? OFFSET ?",
                (session_id, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM audit_entries ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()

        entries = [AuditEntry.from_row(r).to_dict() for r in rows]

        count_row = conn.execute("SELECT COUNT(*) as cnt FROM audit_entries").fetchone()
        total = count_row["cnt"] if count_row else 0
    finally:
        conn.close()

    return {"entries": entries, "total": total, "limit": limit, "offset": offset}


@router.get("/audit/{entry_id}")
async def get_audit(entry_id: str):
    conn = get_connection()
    try:
        entry = get_audit_entry(conn, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Audit entry not found")

        request = get_gate_request(conn, entry.request_id)
        decision = get_gate_decision(conn, entry.decision_id)

        if not request or not decision:
            raise HTTPException(status_code=404, detail="Related records not found")

        signature_valid = verify(entry, request, decision)
    finally:
        conn.close()

    return {
        "entry": entry.to_dict(),
        "request": request.to_dict(),
        "decision": decision.to_dict(),
        "signature_valid": signature_valid,
    }
