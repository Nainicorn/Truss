from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.database import get_connection, init_db
from backend.app.websocket import escalation_manager, decision_manager
from backend.api.gate import router as gate_router
from backend.api.audit import router as audit_router
from backend.api.sessions import router as sessions_router

# Resolve the static frontend build directory
_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = _ROOT / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    init_db(conn)
    conn.close()
    yield


app = FastAPI(
    title="Truss",
    description="Agent Safety Middleware",
    version="0.1.0",
    lifespan=lifespan,
)

_cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(gate_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "truss"}


@app.websocket("/ws/escalations")
async def escalation_ws(websocket: WebSocket):
    accepted = await escalation_manager.connect(websocket)
    if not accepted:
        return
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        escalation_manager.disconnect(websocket)


@app.websocket("/ws/decisions")
async def decision_ws(websocket: WebSocket):
    accepted = await decision_manager.connect(websocket)
    if not accepted:
        return
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        decision_manager.disconnect(websocket)


# Serve frontend static files (production build)
if STATIC_DIR.is_dir():
    # Mount assets directory for JS/CSS bundles
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    # Catch-all: serve index.html for SPA routing
    _STATIC_ROOT = STATIC_DIR.resolve()

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Resolve and verify the path stays within STATIC_DIR (prevent traversal)
        file_path = (STATIC_DIR / full_path).resolve()
        if full_path and str(file_path).startswith(str(_STATIC_ROOT)) and file_path.is_file():
            return FileResponse(str(file_path))
        # Fall back to index.html for SPA routes
        return FileResponse(str(STATIC_DIR / "index.html"))
