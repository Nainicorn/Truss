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

### Phase 3: Demo Agent — COMPLETE (2026-02-26)

**Step 11: Dangerous agent + tools**
- `demo_agent/tools.py` — 3 simulated tools (delete_files, send_email, exec_command) with `TOOL_REGISTRY` mapping to Truss actions
- `demo_agent/agent.py` — `DemoAgent` class with `TRUSS_ENABLED` toggle, session management, scenario runner
- `TRUSS_ENABLED=false` → agent executes every tool call unchecked

**Step 12: Truss integration in agent**
- `TRUSS_ENABLED=true` → every tool call routed through `POST /api/gate` via Python SDK
- Blocked actions abort with reason, escalated actions pause
- Fail-safe: if Truss server unreachable, agent aborts (never defaults to approve)

**Step 13: Scenarios**
- `demo_agent/scenarios/email_injection.py` — CEO spoofed email with "ignore previous instructions" injection → exfiltrates SSH key
- `demo_agent/scenarios/file_exfiltration.py` — hidden instructions in document context → reads /etc/shadow, POSTs to attacker, covers tracks
- Both scenarios verified: without Truss = all actions execute; with Truss = injection blocked, critical actions blocked, high/medium escalated
- `demo_agent/CLAUDE.md` — running instructions and architecture notes

**Backend tests: 120 passing, zero failures (unchanged)**

### Phase 4: Frontend — COMPLETE (2026-02-26)

**Step 14: App shell + routing**
- Full CSS design system per DESIGN.md: tokens, layout, components, animations
- Syne/IBM Plex Mono/DM Sans typography, dark theme only
- Hash-based SPA router with page lifecycle cleanup
- App shell: sidebar nav (Dashboard, Audit Log, Demo) with WS status indicator
- API client: fetch wrapper + WebSocket helpers
- Vite build clean: 16 modules, 0 errors

**Step 15: Dashboard — live decision feed**
- WebSocket `/ws/decisions` for real-time decision streaming (new backend endpoint)
- Decision cards with blast radius badges (6-segment fill), injection alerts
- Summary bar: approved/escalated/blocked count
- Seeds feed from audit API on load, streams new decisions via WS
- Auto-reconnect on disconnect, radar ring background motif

**Step 16: Demo page — side-by-side**
- Two scenarios: Email Injection, File Exfiltration
- Left panel ("Without Truss"): all actions execute unchecked
- Right panel ("With Truss"): calls POST /api/gate, shows block/escalate
- Creates session per run, color-coded event feed

**Step 17: Audit viewer**
- Filterable table: decision type + session dropdown
- Click-to-expand inline detail: Layer 1/2 results, context, HMAC signature
- Blast radius badge in table rows, pagination
- Sessions auto-populated from API

**Backend additions for frontend:**
- `WS /ws/decisions` — broadcasts all gate decisions (not just escalations)
- `decision_manager` singleton in websocket.py
- Gate API broadcasts full decision payload over decisions WS

**Total: 120 backend tests passing, zero failures (unchanged)**

## Next Up

### Phase 5: Deploy + Polish

**Step 18: Deploy to Railway/Render**
- Public URL, everything works cold

**Step 19: README + demo video embed**
- Someone unfamiliar could run this in 5 minutes

**Step 20: Security hardening pass**
- Spawn security auditor subagent against full deployed system

## Environment Notes
- Python 3.9.6 (system python3, no venv)
- Dependencies installed via `python3 -m pip install`
- Vite + vanilla JS frontend (no framework)
