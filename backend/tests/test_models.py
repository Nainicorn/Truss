import os
import tempfile
import pytest

from backend.app.database import get_connection, init_db
from backend.models.gate import (
    Session,
    GateRequest,
    GateDecision,
    AuditEntry,
    insert_session,
    get_session,
    insert_gate_request,
    get_gate_request,
    insert_gate_decision,
    get_gate_decision,
    insert_audit_entry,
    get_audit_entry,
)


@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = get_connection(path)
    init_db(conn)
    yield conn
    conn.close()
    os.unlink(path)


class TestSession:
    def test_insert_and_read(self, db):
        s = Session(agent_id="test-agent", metadata={"env": "test"})
        insert_session(db, s)
        loaded = get_session(db, s.id)
        assert loaded is not None
        assert loaded.id == s.id
        assert loaded.agent_id == "test-agent"
        assert loaded.metadata == {"env": "test"}

    def test_get_nonexistent(self, db):
        assert get_session(db, "nonexistent") is None


class TestGateRequest:
    def test_insert_and_read(self, db):
        s = Session(agent_id="agent-1")
        insert_session(db, s)

        req = GateRequest(
            action="filesystem.delete",
            session_id=s.id,
            params={"path": "/tmp/important"},
            context="user asked to clean up files",
        )
        insert_gate_request(db, req)
        loaded = get_gate_request(db, req.id)
        assert loaded is not None
        assert loaded.action == "filesystem.delete"
        assert loaded.session_id == s.id
        assert loaded.params == {"path": "/tmp/important"}
        assert loaded.context == "user asked to clean up files"

    def test_get_nonexistent(self, db):
        assert get_gate_request(db, "nonexistent") is None


class TestGateDecision:
    def test_insert_and_read(self, db):
        s = Session(agent_id="agent-1")
        insert_session(db, s)
        req = GateRequest(action="shell.exec", session_id=s.id)
        insert_gate_request(db, req)

        dec = GateDecision(
            request_id=req.id,
            decision="block",
            confidence=0.98,
            blast_radius="critical",
            reversible=False,
            injection_detected=True,
            reason="Instruction override detected in context",
            layer_results={"scanner": {"pattern": "instruction_override", "score": 0.95}},
        )
        insert_gate_decision(db, dec)
        loaded = get_gate_decision(db, dec.id)
        assert loaded is not None
        assert loaded.decision == "block"
        assert loaded.confidence == 0.98
        assert loaded.blast_radius == "critical"
        assert loaded.reversible is False
        assert loaded.injection_detected is True
        assert loaded.reason == "Instruction override detected in context"
        assert loaded.layer_results["scanner"]["pattern"] == "instruction_override"

    def test_get_nonexistent(self, db):
        assert get_gate_decision(db, "nonexistent") is None


class TestAuditEntry:
    def test_insert_and_read(self, db):
        s = Session(agent_id="agent-1")
        insert_session(db, s)
        req = GateRequest(action="email.send", session_id=s.id)
        insert_gate_request(db, req)
        dec = GateDecision(
            request_id=req.id,
            decision="escalate",
            confidence=0.75,
            blast_radius="medium",
            reversible=False,
            injection_detected=False,
            reason="Irreversible medium blast radius action",
        )
        insert_gate_decision(db, dec)

        entry = AuditEntry(
            request_id=req.id,
            decision_id=dec.id,
            signature="hmac-sha256:abc123",
        )
        insert_audit_entry(db, entry)
        loaded = get_audit_entry(db, entry.id)
        assert loaded is not None
        assert loaded.request_id == req.id
        assert loaded.decision_id == dec.id
        assert loaded.signature == "hmac-sha256:abc123"

    def test_get_nonexistent(self, db):
        assert get_audit_entry(db, "nonexistent") is None


class TestDatabaseInit:
    def test_tables_exist(self, db):
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        assert "sessions" in table_names
        assert "gate_requests" in table_names
        assert "gate_decisions" in table_names
        assert "audit_entries" in table_names

    def test_foreign_keys_enabled(self, db):
        result = db.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1
