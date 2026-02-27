from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/audit")
async def list_audit():
    return {"entries": []}


@router.get("/audit/{entry_id}")
async def get_audit(entry_id: str):
    return {"entry": None}
