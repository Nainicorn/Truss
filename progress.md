# Truss — Progress Log

## Completed

### Phase 1: Core Safety Engine — COMPLETE (2026-02-26)

**Step 1: DB + Models**
- `backend/app/config.py` — settings from env vars with safe defaults
- `backend/app/database.py` — SQLite connection, WAL mode, foreign keys, schema init
- `backend/models/gate.py` — 4 dataclasses with insert/get operations, JSON serialization
- 10 tests passing

**Step 2: FastAPI skeleton + health endpoint**
- `backend/app/main.py` — FastAPI app with CORS, lifespan DB init
- `backend/api/gate.py`, `audit.py`, `sessions.py` — routers (gate wired, others placeholder)
- 4 tests passing

**Step 3: Action Classifier + taxonomy**
- `backend/classifier/taxonomy.py` — 16 action definitions across 5 categories
- `backend/classifier/action_classifier.py` — deterministic lookup with alias resolution, fail-safe defaults
- 25 tests: all taxonomy entries, aliases, edge cases (case-insensitive, whitespace, unknown)

**Step 4: Injection Scanner + fixtures**
- `backend/scanner/injection_scanner.py` — 5 pattern categories, confidence scoring
- `fixtures/injection_samples.json` — 10 injection samples (all detected)
- `fixtures/benign_samples.json` — 10 benign samples (zero false positives)
- 10 tests passing

**Step 5: Decision Engine**
- `backend/engine/decision_engine.py` — combines classifier + scanner into approve/block/escalate
- Priority rules: injection → critical blast → high blast → medium blast → approve
- 22 tests covering all decision paths

**Step 6: Gate API end-to-end**
- `POST /api/gate` wired to full pipeline with Pydantic validation
- 8 end-to-end API tests: injection→block, critical→block, safe→approve, escalate, aliases, 422

**Total: 79 tests passing, zero failures**

### Phase 2: Audit + Sessions + SDK — COMPLETE (2026-02-26)

**Step 7: Audit trail (HMAC-signed)**
- `backend/audit/trail.py` — HMAC-SHA256 signing and verification
- Gate API now persists requests, decisions, and signed audit entries to DB
- `GET /api/audit` — query audit log with pagination and session filtering
- `GET /api/audit/:id` — full detail with signature verification
- Tamper detection: modifying a decision invalidates its audit signature
- `backend/tests/conftest.py` — test database setup for API tests
- 15 tests passing

**Step 8: Sessions API**
- `POST /api/sessions` — register sessions with agent_id and metadata
- `GET /api/sessions` — list sessions with pagination
- `GET /api/sessions/:id` — session detail with gate requests and decisions
- Gate requests with session_id tied to sessions via foreign key
- Audit entries filterable by session_id
- 10 tests passing

**Step 9: WebSocket escalation stream**
- `backend/app/websocket.py` — EscalationManager with broadcast to all connected clients
- `WS /ws/escalations` — real-time escalation events via WebSocket
- Gate API fires event when decision = "escalate" (not on approve or block)
- Events include action, reason, blast_radius, confidence, session_id
- 7 tests passing

**Step 10: Python SDK**
- `sdk/python/truss_sdk.py` — thin client with `gate()`, `create_session()`, `health()`
- `GateDecision` dataclass with `is_allowed`/`is_blocked`/`is_escalated` helpers
- Zero dependencies — stdlib urllib only
- `TrussError` for API errors, `ConnectionError` for unreachable server
- 11 tests against live server

**Total: 120 tests passing, zero failures**

## Next Up

### Phase 3: Demo Agent

**Step 11: Dangerous agent + tools**
- `demo_agent/agent.py` — agent with dangerous tool capabilities
- `demo_agent/tools.py` — delete_files, send_email, exec_command
- `TRUSS_ENABLED=false` → agent executes everything unchecked

**Step 12: Truss integration in agent**
- `TRUSS_ENABLED=true` → agent routes all actions through Truss gate
- Blocked actions abort, escalations pause for approval

**Step 13: File exfiltration scenario**
- `demo_agent/scenarios/email_injection.py` — injection via email context
- `demo_agent/scenarios/file_exfiltration.py` — data exfil attempt
- Side-by-side demo: with vs without Truss

## Environment Notes
- Python 3.9.6 (system python3, no venv)
- Dependencies installed via `python3 -m pip install`
- Vite scaffold exists for frontend (untouched so far)
