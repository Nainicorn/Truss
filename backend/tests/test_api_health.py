from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "truss"


@pytest.mark.asyncio
async def test_gate_placeholder():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/gate")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_audit_placeholder():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/audit")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_sessions_placeholder():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/sessions")
    assert resp.status_code == 200
