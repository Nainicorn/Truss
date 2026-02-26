from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import uuid
import sqlite3


def _new_id() -> str:
    return uuid.uuid4().hex


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Data classes ---

@dataclass
class Session:
    id: str = field(default_factory=_new_id)
    agent_id: str = ""
    created_at: str = field(default_factory=_now)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["metadata"] = json.dumps(d["metadata"])
        return d

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Session":
        return cls(
            id=row["id"],
            agent_id=row["agent_id"] or "",
            created_at=row["created_at"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )


@dataclass
class GateRequest:
    action: str
    id: str = field(default_factory=_new_id)
    session_id: str = ""
    params: dict = field(default_factory=dict)
    context: str = ""
    received_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["params"] = json.dumps(d["params"])
        return d

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "GateRequest":
        return cls(
            id=row["id"],
            session_id=row["session_id"] or "",
            action=row["action"],
            params=json.loads(row["params"]) if row["params"] else {},
            context=row["context"] or "",
            received_at=row["received_at"],
        )


@dataclass
class GateDecision:
    decision: str
    confidence: float
    blast_radius: str
    reversible: bool
    injection_detected: bool
    reason: str
    id: str = field(default_factory=_new_id)
    request_id: str = ""
    layer_results: dict = field(default_factory=dict)
    decided_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["layer_results"] = json.dumps(d["layer_results"])
        return d

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "GateDecision":
        return cls(
            id=row["id"],
            request_id=row["request_id"] or "",
            decision=row["decision"],
            confidence=row["confidence"],
            blast_radius=row["blast_radius"],
            reversible=bool(row["reversible"]),
            injection_detected=bool(row["injection_detected"]),
            reason=row["reason"],
            layer_results=json.loads(row["layer_results"]) if row["layer_results"] else {},
            decided_at=row["decided_at"],
        )


@dataclass
class AuditEntry:
    signature: str
    id: str = field(default_factory=_new_id)
    request_id: str = ""
    decision_id: str = ""
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "AuditEntry":
        return cls(
            id=row["id"],
            request_id=row["request_id"] or "",
            decision_id=row["decision_id"] or "",
            signature=row["signature"],
            created_at=row["created_at"],
        )


# --- Database operations ---

def insert_session(conn: sqlite3.Connection, session: Session) -> Session:
    d = session.to_dict()
    conn.execute(
        "INSERT INTO sessions (id, agent_id, created_at, metadata) VALUES (:id, :agent_id, :created_at, :metadata)",
        d,
    )
    conn.commit()
    return session


def get_session(conn: sqlite3.Connection, session_id: str) -> Session | None:
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return Session.from_row(row) if row else None


def insert_gate_request(conn: sqlite3.Connection, req: GateRequest) -> GateRequest:
    d = req.to_dict()
    conn.execute(
        "INSERT INTO gate_requests (id, session_id, action, params, context, received_at) "
        "VALUES (:id, :session_id, :action, :params, :context, :received_at)",
        d,
    )
    conn.commit()
    return req


def get_gate_request(conn: sqlite3.Connection, request_id: str) -> GateRequest | None:
    row = conn.execute("SELECT * FROM gate_requests WHERE id = ?", (request_id,)).fetchone()
    return GateRequest.from_row(row) if row else None


def insert_gate_decision(conn: sqlite3.Connection, decision: GateDecision) -> GateDecision:
    d = decision.to_dict()
    conn.execute(
        "INSERT INTO gate_decisions (id, request_id, decision, confidence, blast_radius, "
        "reversible, injection_detected, reason, layer_results, decided_at) "
        "VALUES (:id, :request_id, :decision, :confidence, :blast_radius, "
        ":reversible, :injection_detected, :reason, :layer_results, :decided_at)",
        d,
    )
    conn.commit()
    return decision


def get_gate_decision(conn: sqlite3.Connection, decision_id: str) -> GateDecision | None:
    row = conn.execute("SELECT * FROM gate_decisions WHERE id = ?", (decision_id,)).fetchone()
    return GateDecision.from_row(row) if row else None


def insert_audit_entry(conn: sqlite3.Connection, entry: AuditEntry) -> AuditEntry:
    d = entry.to_dict()
    conn.execute(
        "INSERT INTO audit_entries (id, request_id, decision_id, signature, created_at) "
        "VALUES (:id, :request_id, :decision_id, :signature, :created_at)",
        d,
    )
    conn.commit()
    return entry


def get_audit_entry(conn: sqlite3.Connection, entry_id: str) -> AuditEntry | None:
    row = conn.execute("SELECT * FROM audit_entries WHERE id = ?", (entry_id,)).fetchone()
    return AuditEntry.from_row(row) if row else None
