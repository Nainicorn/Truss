# Rules

- **Always ask the user before compacting context.** Never auto-compact without explicit approval.

---

# Frontend Component Architecture (User Preference)

Follow the patterns from the user's `punk-app` project (`/Users/nainicorn/Documents/punk-app`) as the reference style.

## 3-File Component Convention

Every component gets its own folder with three files:

```
component-name/
├── component-name.js    # Logic, lifecycle, event binding
├── component-name.hbs   # Handlebars template
└── component-name.css   # Scoped styles
```

## Layout Component (Per-Screen Shell)

Every project has a **layout component** that defines the screen structure. The layout changes per context — login shows a different header/body than the dashboard, which differs from the run viewer, etc. Layout acts as the persistent shell that mounts child components into designated containers.

## Component Breakdown

Components are organized by **function**, not by generic names like "body":

| Component | Purpose |
|-----------|---------|
| **layout** | Screen shell — swaps structure per page context (login vs dashboard vs run viewer) |
| **login** | Authentication screen |
| **header** | Top bar — appearance and behavior changes per layout context |
| **sidebar** | Navigation/controls panel |
| **chatbot** | Chat/agent interaction interface |
| **results** | Task/run results display |
| **live-screen** | Real-time execution viewer |
| **data** | Data tables, metrics, evidence browser |

*(Components will evolve as Helm is built — the above are examples of the naming style.)*

## Key Patterns (from punk-app)

- **Conditional Handlebars blocks**: Templates use `{{#if main}}`, `{{#if menu}}` etc. for multi-view rendering from a single template
- **Double-underscore CSS classes**: `.__component-name`, `.__component-name-child` for scoped styling
- **Underscore-prefixed private methods**: `_bindEvents()`, `_loadData()`
- **Pub/sub messaging**: Components communicate via a message bus, not direct imports
- **Data attributes for state**: `data-action`, `data-id`, `data-collapsed` etc.
- **Native `<dialog>` for modals**: Settings, forms, confirmations use `.showModal()`
- **`insertAdjacentHTML()`** for dynamic DOM updates
- **No framework** — vanilla JS, ES6 modules, Handlebars, CSS

---

# Helm — AgentOps Platform

## What This Is

Helm is a production-oriented platform for running, verifying, and governing autonomous AI workflows. Users submit tasks, an AI agent plans and executes them using tools (browser automation, APIs, files, code), with evidence-backed verification, human oversight, and full audit trails.

**MVP target**: User submits a task in the UI → backend plans it → agent executes steps with tools → user sees real-time progress + results with evidence.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Vanilla JS (ES6 Modules), Handlebars, CSS, Vite |
| **Backend** | Python, FastAPI, Pydantic, SQLModel/SQLAlchemy, WebSockets |
| **Workers** | Node.js, Playwright |
| **Storage** | PostgreSQL (Supabase), Supabase Storage (evidence), Redis (Upstash) |
| **AI/Agents** | LangGraph, OpenAI/Anthropic, MCP-style tool registry |
| **Deployment** | AWS Amplify (Frontend), AWS App Runner (Backend), Docker Compose (Local Dev) |

---

## Data Model

```
Task          → top-level user request ("Apply to 10 internships")
├── Run       → single execution attempt of a Task
│   ├── Step  → individual action within a Run ("Search Indeed for jobs")
│   │   ├── Evidence  → proof artifacts (screenshots, DOM snapshots, API responses)
│   │   └── ToolCall  → record of tool invocation (browser, API, file, code)
│   └── Event → streaming execution events (for real-time UI)
├── Policy    → governance rules (permissions, approval requirements)
└── Template  → reusable workflow definition
```

**Key fields**:
- Task: `id, title, description, permissions, status, created_at, user_id`
- Run: `id, task_id, status, plan, started_at, completed_at, metrics`
- Step: `id, run_id, index, action, status, input, output, evidence_ids, started_at, completed_at`
- Evidence: `id, step_id, type (screenshot|dom|artifact|log), url, metadata, created_at`
- Event: `id, run_id, step_id, type, payload, timestamp`

---

## API Endpoints

```
POST   /api/tasks                → create a new task
GET    /api/tasks                → list tasks (with filters)
GET    /api/tasks/:id            → get task detail
POST   /api/tasks/:id/runs       → start a new run
GET    /api/runs/:id             → get run detail with steps
GET    /api/runs/:id/steps       → list steps for a run
GET    /api/runs/:id/evidence    → list evidence for a run
POST   /api/runs/:id/approve     → human approval for pending step
POST   /api/runs/:id/cancel      → cancel a running execution
WS     /ws/runs/:id              → real-time event stream for a run
GET    /api/metrics              → aggregate stats
POST   /api/templates            → save run as template
POST   /api/templates/:id/run    → execute a template
GET    /api/health               → health check
```

---

## Repository Structure

```
helm/
├── src/                         # Frontend (Vite at repo root)
│   ├── main.js                  # App entry, router init
│   ├── router.js                # Hash-based SPA router
│   ├── api/
│   │   └── client.js            # Fetch wrapper + WebSocket manager
│   ├── pages/
│   │   ├── dashboard.js         # Task list, metrics summary
│   │   ├── taskNew.js           # Task submission form
│   │   ├── taskDetail.js        # Task detail + run history
│   │   └── runDetail.js         # Live run viewer
│   ├── components/
│   │   ├── layout.js            # Shell (sidebar, header, content)
│   │   ├── stepCard.js          # Individual step display
│   │   ├── evidenceViewer.js    # Screenshot/artifact viewer
│   │   ├── timeline.js          # Execution timeline
│   │   └── statusBadge.js       # Status indicator
│   ├── templates/               # Handlebars .hbs templates
│   ├── styles/                  # CSS files
│   └── utils/
│       └── helpers.js           # Formatting, date, etc.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory, CORS, startup
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── events.py            # Redis pub/sub event bus
│   │   └── websocket.py         # WebSocket endpoint
│   ├── api/
│   │   ├── tasks.py             # Task CRUD endpoints
│   │   └── runs.py              # Run management endpoints
│   ├── orchestrator/
│   │   ├── graph.py             # LangGraph StateGraph definition
│   │   ├── planner.py           # LLM-based task planner
│   │   ├── executor.py          # Step execution node
│   │   ├── approval.py          # Human-in-the-loop gate
│   │   └── tools/
│   │       ├── registry.py      # MCP-style tool registry
│   │       ├── browser.py       # Playwright browser automation
│   │       ├── api_call.py      # HTTP API tool
│   │       └── file.py          # File read/write tool
│   ├── verifier/
│   │   ├── verify.py            # Verification node
│   │   └── checks.py            # Verification strategies
│   ├── models/
│   │   ├── task.py              # Task, Run, Step, Evidence SQLModels
│   │   ├── policy.py            # Policy model
│   │   └── template.py          # Template model
│   ├── requirements.txt
│   └── tests/
├── workers/
│   └── playwright/
│       ├── index.js             # Browser automation worker
│       └── actions.js           # Navigate, click, fill, screenshot
├── infra/
│   └── docker/
│       ├── Dockerfile.backend
│       └── Dockerfile.workers
├── docker-compose.yml
├── .env.example
├── index.html
├── package.json
└── CLAUDE.md                    # This file
```

---

## Agent Orchestration (LangGraph)

```
                    ┌─────────┐
                    │ Planner │  ← breaks task into steps
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │Approval │  ← human-in-the-loop gate (if policy requires)
                    └────┬────┘
                         │
                    ┌────▼─────┐
                    │ Executor │  ← runs tools (browser, API, file, code)
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ Verifier │  ← checks evidence, validates output
                    └────┬─────┘
                         │
                    ┌────▼────┐
               ┌────│ Router  │────┐
               │    └─────────┘    │
          more steps          all done
               │                   │
               ▼                   ▼
          [Executor]         ┌──────────┐
                             │ Reporter │  ← generates summary/report
                             └──────────┘
```

**State schema**: `{ task, plan, current_step_index, steps, evidence, status, messages }`

---

## Build Phases

### Phase 1: Project Scaffolding & Core Structure
- Restructure `src/` — router, layout shell, CSS foundation, Handlebars pipeline
- Backend — FastAPI app, config, SQLModel models (Task, Run, Step, Evidence), CRUD endpoints
- Infra — `docker-compose.yml` (PostgreSQL + Redis + backend + frontend), `.env.example`
- **Demo**: Frontend shell renders with navigation. Backend returns task list. Docker boots everything.

### Phase 2: Task Submission & Planning
- Backend — `orchestrator/planner.py` (LLM-based), `orchestrator/graph.py` (planner node), OpenAI/Anthropic integration
- Frontend — Task submission form, task detail page showing plan, API client
- **Demo**: User submits "Apply to 5 internships" → sees structured step plan.

### Phase 3: Execution Engine & Tool System
- Backend — `orchestrator/executor.py`, tool registry, browser/API/file tools, LangGraph graph expansion
- Workers — Playwright worker (`workers/playwright/`), navigate/click/fill/screenshot actions
- **Demo**: Submit task → plan generated → agent executes steps → status updates in DB.

### Phase 4: Real-Time Streaming & Live UI
- Backend — Redis pub/sub event bus, WebSocket endpoint, orchestrator emits events
- Frontend — WebSocket manager, live-updating run detail page, timeline, status animations
- **Demo**: Start a run → watch steps execute in real-time in the UI.

### Phase 5: Evidence & Verification
- Backend — Verifier node in graph, verification strategies, evidence capture to Supabase Storage
- Frontend — Evidence viewer (lightbox), verification badges, evidence browser page
- **Demo**: Steps show screenshots/artifacts. Verification badges confirm results.

### Phase 6: Human-in-the-Loop & Governance
- Backend — Policy model, approval gate node, policy engine
- Frontend — Approval dialog, policy config UI, notification indicators, audit log
- **Demo**: Agent pauses at high-risk step → user approves → execution continues.

### Phase 7: Dashboard, Metrics & Templates
- Backend — `/api/metrics`, Template model, save/run template endpoints
- Frontend — Dashboard with filters/search, metrics cards, template gallery
- **Demo**: Dashboard shows aggregate metrics. Save and re-run workflow templates.

### Phase 8: Production Hardening & Deployment
- Infra — Production Dockerfiles, AWS Amplify/App Runner config, CI/CD (GitHub Actions)
- Backend — Auth (Supabase Auth), rate limiting, structured logging, Alembic migrations
- Frontend — Error boundaries, offline handling, performance optimization
- **Demo**: Full platform running on AWS with authentication.

---

## Critical Files (Build Order)

| File | Why |
|------|-----|
| `src/router.js` | Foundation of all frontend navigation |
| `src/api/client.js` | All frontend-backend communication |
| `backend/app/main.py` | FastAPI entry point — all routes attach here |
| `backend/models/task.py` | Core data domain — every endpoint reads/writes these |
| `backend/orchestrator/graph.py` | LangGraph StateGraph — heart of agent execution |
| `backend/app/events.py` | Bridge between orchestrator and WebSocket streaming |
| `docker-compose.yml` | Local dev environment for all services |

---

## Conventions

- Frontend uses vanilla JS with ES6 modules — no frameworks
- Handlebars for HTML templating, compiled at build time via Vite plugin
- Hash-based routing (`#/tasks/new`, `#/runs/:id`)
- Backend follows FastAPI best practices — routers, dependency injection, Pydantic schemas
- All models use SQLModel (SQLAlchemy + Pydantic hybrid)
- Agent orchestration via LangGraph StateGraph with typed state
- Events use Redis pub/sub, streamed to frontend via WebSocket
- Evidence stored in Supabase Storage, referenced by URL in DB

## Commands

```bash
# Frontend
npm run dev          # Start Vite dev server (localhost:5173)
npm run build        # Production build
npm run preview      # Preview production build

# Backend
cd backend && uvicorn app.main:app --reload    # Start FastAPI (localhost:8000)
pytest backend/tests/                           # Run backend tests

# Full stack
docker compose up    # Boot all services
```
