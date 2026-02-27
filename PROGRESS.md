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

## Next Up

### Phase 2: Audit + Sessions + SDK

**Step 7: Audit trail (HMAC-signed)**
- HMAC-sign every gate decision
- Store in audit_entries table
- `GET /api/audit` — query audit log
- `GET /api/audit/:id` — single entry with signature verification
- Verify signature integrity on each entry

**Step 8: Sessions API**
- `POST /api/sessions` — register a session
- `GET /api/sessions` — list sessions
- `GET /api/sessions/:id` — session detail with gate requests
- Tie gate requests to sessions

**Step 9: WebSocket escalation stream**
- `WS /ws/escalations` — real-time escalation events
- Fire event when decision = escalate

**Step 10: Python SDK**
- `sdk/python/truss_sdk.py` — thin client, one method: `truss.gate()`
- Returns full decision object

## Environment Notes
- Python 3.9.6 (system python3, no venv)
- Dependencies installed via `python3 -m pip install`
- Vite scaffold exists for frontend (untouched so far)
