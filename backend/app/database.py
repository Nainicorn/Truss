from __future__ import annotations

import sqlite3
import os
from backend.app.config import settings


def get_db_path() -> str:
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///"):]
    return url


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            agent_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSON
        );

        CREATE TABLE IF NOT EXISTS gate_requests (
            id TEXT PRIMARY KEY,
            session_id TEXT REFERENCES sessions(id),
            action TEXT NOT NULL,
            params JSON,
            context TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS gate_decisions (
            id TEXT PRIMARY KEY,
            request_id TEXT REFERENCES gate_requests(id),
            decision TEXT NOT NULL,
            confidence REAL NOT NULL,
            blast_radius TEXT NOT NULL,
            reversible BOOLEAN NOT NULL,
            injection_detected BOOLEAN NOT NULL,
            reason TEXT NOT NULL,
            layer_results JSON,
            decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_entries (
            id TEXT PRIMARY KEY,
            request_id TEXT REFERENCES gate_requests(id),
            decision_id TEXT REFERENCES gate_decisions(id),
            signature TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
