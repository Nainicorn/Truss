# Truss — Progress Log

## Completed

### Step 1: DB + Models (2026-02-26)
- Created full directory structure per CLAUDE.md repo layout
- Built `backend/app/config.py` — settings from env vars with safe defaults
- Built `backend/app/database.py` — SQLite connection, WAL mode, foreign keys, schema init
- Built `backend/models/gate.py` — 4 dataclasses (Session, GateRequest, GateDecision, AuditEntry) with insert/get operations, JSON serialization, and row mapping
- Built `backend/tests/test_models.py` — 10 tests covering all models CRUD + schema verification
- All tests passing, import + insert/read verified
- Python 3.9 compatible (using `from __future__ import annotations`)

## Next Up

### Step 2: FastAPI skeleton + health endpoint
- `backend/app/main.py` — FastAPI app with CORS, lifespan (init DB on startup)
- `backend/api/gate.py` — placeholder router
- `backend/api/audit.py` — placeholder router
- `backend/api/sessions.py` — placeholder router
- Verify: `curl localhost:8000/api/health` returns 200

## Environment Notes
- Python 3.9.6 (system python3, no venv)
- Dependencies installed via `python3 -m pip install`
- Vite scaffold exists for frontend (untouched so far)
