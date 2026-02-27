from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app


@pytest.fixture
def transport():
    return ASGITransport(app=app)


class TestCreateSession:
    @pytest.mark.asyncio
    async def test_create_session(self, transport):
        """POST /api/sessions creates a new session."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/sessions", json={
                "agent_id": "demo-agent-1",
                "metadata": {"env": "test", "version": "1.0"},
            })
        assert resp.status_code == 200
        data = resp.json()
        session = data["session"]
        assert session["agent_id"] == "demo-agent-1"
        assert session["metadata"] == {"env": "test", "version": "1.0"}
        assert "id" in session
        assert "created_at" in session

    @pytest.mark.asyncio
    async def test_create_session_minimal(self, transport):
        """POST /api/sessions with empty body creates session with defaults."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/sessions", json={})
        assert resp.status_code == 200
        session = resp.json()["session"]
        assert session["agent_id"] == ""
        assert session["metadata"] == {}


class TestListSessions:
    @pytest.mark.asyncio
    async def test_list_empty(self, transport):
        """GET /api/sessions with no sessions returns empty list."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sessions"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_after_create(self, transport):
        """GET /api/sessions returns created sessions."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post("/api/sessions", json={"agent_id": "agent-a"})
            await client.post("/api/sessions", json={"agent_id": "agent-b"})
            resp = await client.get("/api/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sessions"]) == 2
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_pagination(self, transport):
        """GET /api/sessions supports limit and offset."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for i in range(5):
                await client.post("/api/sessions", json={"agent_id": f"agent-{i}"})
            resp = await client.get("/api/sessions?limit=2&offset=0")
        data = resp.json()
        assert len(data["sessions"]) == 2
        assert data["total"] == 5


class TestGetSession:
    @pytest.mark.asyncio
    async def test_get_session_detail(self, transport):
        """GET /api/sessions/:id returns session with request history."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            create_resp = await client.post("/api/sessions", json={
                "agent_id": "demo-agent",
            })
            session_id = create_resp.json()["session"]["id"]

            resp = await client.get(f"/api/sessions/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session"]["id"] == session_id
        assert data["session"]["agent_id"] == "demo-agent"
        assert data["requests"] == []
        assert data["request_count"] == 0

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, transport):
        """GET /api/sessions/:id with bad ID returns 404."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/sessions/nonexistent")
        assert resp.status_code == 404


class TestSessionGateIntegration:
    @pytest.mark.asyncio
    async def test_gate_request_tied_to_session(self, transport):
        """Gate requests with session_id appear in session detail."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create a session
            create_resp = await client.post("/api/sessions", json={
                "agent_id": "integration-agent",
            })
            session_id = create_resp.json()["session"]["id"]

            # Make gate requests tied to this session
            await client.post("/api/gate", json={
                "action": "filesystem.read",
                "session_id": session_id,
                "context": "Read a file.",
            })
            await client.post("/api/gate", json={
                "action": "email.send",
                "session_id": session_id,
                "params": {"to": "user@example.com"},
            })

            # Check session detail shows both requests
            resp = await client.get(f"/api/sessions/{session_id}")
        data = resp.json()
        assert data["request_count"] == 2
        actions = [r["request"]["action"] for r in data["requests"]]
        assert "filesystem.read" in actions
        assert "email.send" in actions

    @pytest.mark.asyncio
    async def test_gate_requests_include_decisions(self, transport):
        """Session detail includes decision for each gate request."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            create_resp = await client.post("/api/sessions", json={
                "agent_id": "decision-agent",
            })
            session_id = create_resp.json()["session"]["id"]

            await client.post("/api/gate", json={
                "action": "shell.exec",
                "session_id": session_id,
                "context": "Run a command.",
            })

            resp = await client.get(f"/api/sessions/{session_id}")
        data = resp.json()
        assert data["request_count"] == 1
        req_detail = data["requests"][0]
        assert req_detail["decision"] is not None
        assert req_detail["decision"]["decision"] == "block"
        assert req_detail["decision"]["blast_radius"] == "critical"

    @pytest.mark.asyncio
    async def test_audit_filter_by_session(self, transport):
        """GET /api/audit?session_id= filters entries by session."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create two sessions
            s1_resp = await client.post("/api/sessions", json={"agent_id": "s1"})
            s2_resp = await client.post("/api/sessions", json={"agent_id": "s2"})
            s1_id = s1_resp.json()["session"]["id"]
            s2_id = s2_resp.json()["session"]["id"]

            # Gate requests to each session
            await client.post("/api/gate", json={"action": "filesystem.read", "session_id": s1_id})
            await client.post("/api/gate", json={"action": "filesystem.read", "session_id": s1_id})
            await client.post("/api/gate", json={"action": "filesystem.read", "session_id": s2_id})

            # Filter audit by session
            resp = await client.get(f"/api/audit?session_id={s1_id}")
        data = resp.json()
        assert len(data["entries"]) == 2
