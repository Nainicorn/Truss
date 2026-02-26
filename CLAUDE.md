# Rules

**Always ask the user before compacting context.** Never auto-compact without explicit approval.
**Commit after every completed build step.** Each commit = a working, testable state.
**Update `progress.md` after every session.** Future sessions depend on it.
**Run tests after every file change.** Never mark a step done without verification.
**Don't try to one-shot complex features.** Break into incremental steps, commit each one.

---

# Helm — Verification-First AgentOps Platform

**MVP target**: Task creation → planner generates step plan → executor runs tools → LLM-judge verifier confirms each step with evidence → WebSocket streams progress to UI → final evidence report viewable in browser.

The core differentiator: **every agent action is verified with evidence before it's marked complete.**

---

## Context Engineering Notes

This file is loaded into context on every turn. Keep it lean. Details that only matter for specific modules belong in subdirectory CLAUDE.md files, not here.

- `backend/CLAUDE.md` — backend-specific conventions, import patterns, test commands
- `src/CLAUDE.md` — frontend conventions, component patterns, CSS approach
- `progress.md` — living progress log (READ THIS FIRST every session)

When context gets long, use `/compact`. When switching between backend and frontend work, use `/clear` and start fresh — the progress file and git history carry the state.

---

## Session Protocol

### First Session (Initializer)
```
Read CLAUDE.md. This is the first session. Set up:
1. Create directory structure per repo structure below
2. Build step 1 from the build order
3. Create progress.md with what was built and what's next
4. Commit with descriptive message
```

### Every Subsequent Session (Incremental Coder)
```
Read CLAUDE.md and progress.md.
Check git log --oneline -10 to see recent work.
Build the next uncompleted step from the build order.
Update progress.md when done.
Commit with descriptive message.
```

### The Agent Loop (every step follows this)
```
Gather Context → Take Action → Verify → Commit
```
1. **Gather**: Read relevant files, check current state, understand what exists
2. **Act**: Write code, create files, make changes
3. **Verify**: Run tests, start the server, curl the endpoint, check the output
4. **Commit**: Git commit with a message describing what was built and verified

Never skip verification. If you can't run tests, at minimum import the module and confirm no syntax errors.

---

## Demo Use Case: Automated Compliance Checking

The flagship demo is **automated compliance checking against a document** — verifiable pass/fail with citations. User submits a compliance check (e.g., "Check privacy policy against GDPR Art. 13"), the planner breaks it into steps, executor parses documents and checks requirements using tools (`file.py`, `browser.py`), the verifier confirms each check via LLM-as-judge with pass/fail citations, and the final output is a compliance report with per-requirement status, evidence links, and audit trail.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Vanilla JS (ES6 Modules), CSS, Vite |
| **Backend** | Python 3.12+, FastAPI, Pydantic, SQLModel/SQLAlchemy, WebSockets |
| **Browser Automation** | playwright-python (in-process, no separate worker) |
| **File Parsing** | PyMuPDF or pdfplumber for document extraction |
| **Storage** | SQLite for MVP (swap to PostgreSQL/Supabase later) |
| **AI** | Anthropic Claude API (planning + LLM-judge verification) |
| **Deployment** | Local dev first, Docker Compose later |

> **What's deferred**: LangGraph, Redis, PostgreSQL, Supabase Storage, eval harness, policy model, approval gate. All recoverable once the core loop works end-to-end.

---

## Data Model

```
Task          → top-level user request ("Check privacy policy against GDPR Art. 13")
├── Run       → single execution attempt of a Task
│   ├── Step  → individual action within a Run ("Extract GDPR Art. 13 requirements")
│   │   ├── Evidence  → proof artifacts (screenshots, text extracts, logs)
│   │   └── ToolCall  → record of tool invocation
│   └── Event → streaming execution events (for real-time UI)
```

### Database Schema (SQLite for MVP)

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    task_id TEXT REFERENCES tasks(id),
    status TEXT DEFAULT 'pending',
    plan JSON,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    metrics JSON
);

CREATE TABLE steps (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES runs(id),
    index_ INTEGER NOT NULL,
    action TEXT NOT NULL,
    tool TEXT,
    status TEXT DEFAULT 'pending',
    input JSON,
    output JSON,
    verification JSON,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    estimated_cost_usd REAL,
    retry_count INTEGER DEFAULT 0
);

CREATE TABLE evidence (
    id TEXT PRIMARY KEY,
    step_id TEXT REFERENCES steps(id),
    type TEXT NOT NULL,
    content TEXT,
    file_path TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Status State Machines

Run: `pending → planning → executing → verifying → completed | failed | cancelled`
Step: `pending → running → verifying → verified | failed | skipped`

---

## API Endpoints (MVP)

```
POST   /api/tasks                → create a new task
GET    /api/tasks                → list tasks
GET    /api/tasks/:id            → get task detail
POST   /api/tasks/:id/runs       → start a new run
GET    /api/runs/:id             → run detail with steps + evidence
POST   /api/runs/:id/cancel      → cancel a running execution
WS     /ws/runs/:id              → real-time event stream
GET    /api/health               → health check
```

---

## Repository Structure

```
helm/
├── src/                         # Frontend (Vite at repo root)
│   ├── main.js
│   ├── router.js                # Hash-based SPA router
│   ├── CLAUDE.md                # Frontend-specific conventions
│   ├── api/
│   │   └── client.js
│   ├── pages/
│   │   ├── dashboard.js
│   │   ├── taskNew.js
│   │   └── runViewer.js         # THE KEY PAGE
│   ├── components/
│   │   ├── layout.js
│   │   ├── stepCard.js
│   │   ├── evidencePanel.js
│   │   ├── timeline.js
│   │   └── statusBadge.js
│   ├── styles/
│   │   ├── base.css
│   │   ├── layout.css
│   │   ├── components.css
│   │   └── run-viewer.css
│   └── utils/
│       └── helpers.js
├── backend/
│   ├── CLAUDE.md                # Backend-specific conventions
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── websocket.py
│   ├── api/
│   │   ├── tasks.py
│   │   └── runs.py
│   ├── orchestrator/
│   │   ├── engine.py
│   │   ├── planner.py
│   │   ├── executor.py
│   │   └── tools/
│   │       ├── registry.py
│   │       ├── browser.py
│   │       ├── api_call.py
│   │       └── file.py
│   ├── verifier/
│   │   └── llm_judge.py
│   ├── models/
│   │   └── task.py
│   ├── requirements.txt
│   └── tests/
├── fixtures/
│   ├── sample_privacy_policy.txt
│   └── gdpr_art13_requirements.json
├── evidence/
├── progress.md           # Living progress log — READ FIRST every session
├── .env.example
├── index.html
├── package.json
└── CLAUDE.md                    # This file
```

---

## Orchestrator Design

Simple async Python orchestrator. No LangGraph. Follows the agent loop: gather context → take action → verify → repeat.

```python
class Orchestrator:
    """
    1. Gather: receive task, read relevant context
    2. Plan: call planner (LLM) → structured list of steps
    3. For each step:
        a. Act: execute step using appropriate tool
        b. Capture: save evidence (screenshots, text extracts)
        c. Verify: call LLM-judge with evidence + expected outcome
        d. Emit: broadcast event via WebSocket
        e. Retry: if failed and retries remain, retry with backoff
    4. Report: compile final evidence report
    """
```

In-memory event broadcasting via asyncio.Queue. No Redis.

**Partial failure**: Each step independently retryable. Max 2 retries with exponential backoff. Error captured as evidence before retry.

---

## Verification System (Technical Centerpiece)

One strategy for MVP: **LLM-as-judge only.**

```python
class LLMJudgeVerifier:
    """
    Sends step output + evidence to Claude.
    Returns: { verified: bool, confidence: float, reasoning: str, citations: list[str] }
    
    Thresholds:
    - >= 0.9 → auto-verified
    - 0.7–0.9 → verified with warning
    - < 0.7 → failed
    """
```

---

## Frontend — The Demo IS the UI

The run viewer is the most important page. Dark theme, clean, monospace accents. Mission control for AI agents.

1. Vertical timeline of steps
2. Each step: index, action, status badge, duration
3. Active steps pulse/animate
4. Verification results appear with smooth transition
5. Click step → expand evidence panel
6. Top: run status, progress bar, elapsed time
7. Bottom: summary metrics on completion

---

## Build Order

Each step = one session (or less). Commit after each. Update `progress.md` after each.

### Phase 1: Backend Core (sessions 1–6)
Use `/clear` between unrelated steps to keep context fresh.

| Step | What to Build | How to Verify |
|------|---------------|---------------|
| 1 | Database + Models — SQLModel, SQLite, CRUD | `python -c "from backend.models.task import *"` + create/read a task |
| 2 | FastAPI skeleton — app factory, health, task CRUD, run endpoints | `curl localhost:8000/api/health` + `curl POST /api/tasks` |
| 3 | Planner — LLM planner: description → structured step list | Call planner with test input, verify JSON structure |
| 4 | Tools — File parser (text extraction from .txt/.pdf) | Parse `fixtures/sample_privacy_policy.txt`, verify output |
| 5 | Orchestrator — async run loop: plan → execute → capture evidence | Start a run via API, check DB for steps + evidence |
| 6 | Verifier — LLM-judge: evidence → verification result | Test on known-pass AND known-fail, confirm it discriminates |

### Phase 2: Real-Time Layer (session 7)
| Step | What to Build | How to Verify |
|------|---------------|---------------|
| 7 | WebSocket streaming — event emitter + WS endpoint | `wscat -c ws://localhost:8000/ws/runs/{id}`, start run, confirm events |

### Phase 3: Frontend (sessions 8–10)
`/clear` before starting. Fresh context for a different domain.

| Step | What to Build | How to Verify |
|------|---------------|---------------|
| 8 | App shell + routing — layout, hash router, nav | Open browser, navigate between routes |
| 9 | Dashboard + Task creation — task list, new task form | Create task via UI, see it in list |
| 10 | Run Viewer — timeline, step cards, evidence, live WS | Start run, watch steps appear real-time |

### Phase 4: Demo + Polish (sessions 11–12)
| Step | What to Build | How to Verify |
|------|---------------|---------------|
| 11 | Demo fixture — privacy policy + GDPR requirements | End-to-end: submit check, see pass/fail results |
| 12 | Polish — error handling, loading states, empty states | Manual walkthrough of all UI states |

---

## Subagent Usage Guide

Use subagents (via Task tool) for:
- **Writer/Reviewer**: After building a component, spawn a fresh-context subagent to review it
- **Parallel work**: One subagent writes test fixtures while main agent builds the code
- **Deep file analysis**: Spawn a subagent to grep/analyze large files without polluting main context

Don't use subagents for simple sequential steps or tasks needing full conversation history.

---

## Demo Fixture

- `fixtures/sample_privacy_policy.txt` — Realistic privacy policy (~2 pages)
- `fixtures/gdpr_art13_requirements.json` — Structured list: `{ id, title, description, keywords }`

Some requirements PASS, some FAIL — proves the verifier discriminates.

---

## Environment Variables

```
ANTHROPIC_API_KEY=sk-...
DATABASE_URL=sqlite:///helm.db
EVIDENCE_DIR=./evidence
```

---

## Conventions

- **Commit often.** Each build step = at least one commit.
- **Test everything.** Never mark done without running it.
- **Progress file is sacred.** Write it like onboarding the next developer.
- Frontend: vanilla JS, make it look sharp — this is the demo.
- Backend: FastAPI best practices, routers, dependency injection, Pydantic schemas.
- Models: SQLModel (SQLAlchemy + Pydantic hybrid).
- Status transitions: explicit and enforced.
- Evidence: stored in `./evidence/`, referenced by path in DB.
- Track `duration_ms` and `estimated_cost_usd` on steps.

## Commands

```bash
# Frontend
npm run dev          # Vite dev server (localhost:5173)
npm run build        # Production build

# Backend
cd backend && uvicorn app.main:app --reload    # FastAPI (localhost:8000)
pytest backend/tests/                           # Run tests

# Quick verify
python -c "from backend.models.task import *"  # Import check
curl http://localhost:8000/api/health           # Health check
```

---

## Future Phases (Deferred)

Add back only after the core loop works end-to-end:

- LangGraph migration, PostgreSQL + Supabase, Redis pub/sub
- Multiple verification strategies (TextMatch, SchemaCheck)
- Human-in-the-loop approval gate
- Policy model, evaluation harness
- Auth, rate limiting, structured logging, CI/CD