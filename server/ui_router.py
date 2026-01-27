"""FastAPI router for UI and health checks.

NOTE: All UI rendering is now handled by the SPA frontend (Vite) running on port 5173.
This router only provides:
- Health check endpoint
- Static file serving for assets

The backend serves API endpoints on /api/* only.
"""

import structlog

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = structlog.get_logger()

router = APIRouter(tags=["ui"])


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        dict with status
    """
    return {"status": "ok"}
