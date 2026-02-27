from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/sessions")
async def list_sessions():
    return {"sessions": []}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    return {"session": None}


@router.post("/sessions")
async def create_session():
    return {"session": None}
