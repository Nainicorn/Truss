from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.app.database import get_connection, init_db
from backend.app.websocket import escalation_manager
from backend.api.gate import router as gate_router
from backend.api.audit import router as audit_router
from backend.api.sessions import router as sessions_router


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gate_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "truss"}


@app.websocket("/ws/escalations")
async def escalation_ws(websocket: WebSocket):
    await escalation_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        escalation_manager.disconnect(websocket)
