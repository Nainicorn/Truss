from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query

from backend.app.database import get_connection
from backend.models.gate import (
    Session,
    GateRequest,
    GateDecision,
    insert_session,
    get_session,
)


router = APIRouter()


class CreateSessionBody(BaseModel):
    agent_id: str = ""
    metadata: dict = Field(default_factory=dict)


@router.post("/sessions")
async def create_session(body: CreateSessionBody):
    session = Session(agent_id=body.agent_id, metadata=body.metadata)
    conn = get_connection()
    try:
        insert_session(conn, session)
    finally:
        conn.close()
    return {"session": _session_to_response(session)}


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        sessions = [_session_to_response(Session.from_row(r)) for r in rows]

        count_row = conn.execute("SELECT COUNT(*) as cnt FROM sessions").fetchone()
        total = count_row["cnt"] if count_row else 0
    finally:
        conn.close()

    return {"sessions": sessions, "total": total, "limit": limit, "offset": offset}


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str):
    conn = get_connection()
    try:
        session = get_session(conn, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Fetch gate requests tied to this session
        req_rows = conn.execute(
            "SELECT * FROM gate_requests WHERE session_id = ? ORDER BY received_at DESC",
            (session_id,),
        ).fetchall()
        requests = []
        for row in req_rows:
            req = GateRequest.from_row(row)
            # Get the associated decision
            dec_row = conn.execute(
                "SELECT * FROM gate_decisions WHERE request_id = ?",
                (req.id,),
            ).fetchone()
            decision = GateDecision.from_row(dec_row) if dec_row else None
            requests.append({
                "request": req.to_dict(),
                "decision": decision.to_dict() if decision else None,
            })
    finally:
        conn.close()

    return {
        "session": _session_to_response(session),
        "requests": requests,
        "request_count": len(requests),
    }


def _session_to_response(session: Session) -> dict:
    """Convert a Session to a JSON-friendly dict (metadata as dict, not JSON string)."""
    return {
        "id": session.id,
        "agent_id": session.agent_id,
        "created_at": session.created_at,
        "metadata": session.metadata,
    }
