from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post("/gate")
async def gate():
    return {"status": "placeholder"}
