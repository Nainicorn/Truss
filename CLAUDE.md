# Polaris (AECF)
**Project:** Polaris — Trace-based Evaluation, Governance, and Self-Correction Framework (AECF)  
**Purpose of this doc:** Instructions for using Claude (or any LLM coding agent) to build Polaris efficiently: token discipline, safe edits, deterministic outputs, and reproducible development.

---

## 0) North Star
Polaris is an **agentic evaluation system** (not a general “agent”). It evaluates candidate agent/model outputs by:
- generating a **ProbePlan** (tests to run)
- executing probes with **evidence**
- labeling failures with a **FailureTaxonomy**
- producing a **Decision**: `ACCEPT / REVISE / CONSTRAIN / ESCALATE`
- persisting a replayable **AuditTrace**

**Success = trust infrastructure.** The system must be auditable, reproducible, and efficient.

---

## 0.5) Build Phases (MANDATORY ORDER)

Polaris must be built in the following phases.  
Do not skip phases. Do not jump ahead.

### Phase 1 — Schema Lock (no agent logic)
Goal:
- Define and validate all core schemas.
Deliverables:
- TaskSpec
- CandidateOutput
- ProbePlan
- ProbeResult
- Decision
- AuditTrace
Rules:
- No LangGraph yet
- No probes yet
- No UI
- All schemas must validate via Pydantic + JSON schema

### Phase 2 — Evaluation Loop (single pass)
Goal:
- Evaluate one candidate output end-to-end.
Deliverables:
- LangGraph state machine
- Nodes: Normalize → ProbePlan → ExecuteProbes → Decide → FinalizeTrace
Rules:
- Max 3 probes
- No revision loop
- CLI execution only
- Structured logging required

### Phase 3 — Persistence + Replay
Goal:
- Make runs durable and debuggable.
Deliverables:
- Postgres storage for runs, probes, decisions, traces
- Deterministic re-run capability
Rules:
- JSONB storage acceptable
- No UI yet

### Phase 4 — Minimal UI (read-only)
Goal:
- Make the system explain itself visually.
Deliverables:
- /runs list
- /runs/{id} detail
Rules:
- Server-rendered HTML
- Handlebars partials
- No client-side state management

### Phase 5 — One Advanced Capability
Goal:
- Demonstrate depth without sprawl.
Pick ONE:
- Tool-call verifier
- Revision loop (max 1 retry)
- Failure taxonomy dashboard
Rules:
- Must integrate cleanly into existing trace
- Must not add new unbounded loops

### Phase 6 — Documentation + Demo
Goal:
- Make the project legible to external readers.
Deliverables:
- README with problem framing + architecture
- Example run walkthrough
- Screenshots or logs

---

## 1) Non-Negotiable Requirements (Project)
### 1.1 Functional requirements
Every evaluation run MUST produce and persist:
- `ProbePlan` (what/why tests)
- `ProbeResults` (verdict + evidence + confidence)
- `FailureTaxonomy` labels (standardized)
- `Decision` object (A/R/C/E)
- `AuditTrace` (replayable timeline incl. node timings and tool events)

The system MUST support:
- small bounded probe plans (default 3–6, cap 8)
- capped revision loop (max 2 iterations)
- tool allowlists per task/rubric
- stable schemas (Pydantic + JSON Schema validation)
- versioning (rubrics/probes/taxonomy/constitution/model config)

### 1.2 Safety and reliability requirements
- No secret leakage in logs/traces (redaction required)
- Timeouts per probe and global run timeout
- Rate limiting on endpoints that trigger model calls
- Idempotency keys / dedupe to avoid duplicate paid runs

### 1.3 UI requirements (no frameworks)
UI must be:
- **Vanilla HTML + Vanilla JS (ES modules) + Handlebars + CSS**
- No React/Next/Vue/Svelte/etc.
- No heavy build pipeline required (esbuild optional only)

Minimum pages:
- `/runs` list with server-side filters via query params
- `/runs/{id}` detail with collapsible probes + evidence viewer + download report
- `/metrics` summary tables (charts optional)

---

## 2) Exact Tech Stack (Project Standard)
### Backend & Infra
- **Python 3.11+**
- **uv** (env/deps)
- **FastAPI** (REST + OpenAPI)
- **Pydantic v2** (schemas)
- **PostgreSQL 16** (JSONB-first storage)
- **Redis** (queue, caching, rate limiting, idempotency)
- **Celery + Redis** (or RQ + Redis, but pick one and standardize)
- **Docker + Compose**

### Agent orchestration
- **LangGraph** state machine for evaluation workflow
- Model provider:
  - OpenAI Responses API OR Anthropic Claude SDK (choose one primary)
- Optional (high-signal):
  - MCP tool layer (standardized tools)

### Observability (strongly recommended)
- Structured logs with run_id correlation
- Optional but great:
  - OpenTelemetry spans per graph node/probe/tool call

### UI (strict)
- HTML5 + CSS
- Vanilla JS (ES2022 modules)
- Handlebars templates/partials
- Optional helpers (not frameworks):
  - esbuild (bundling/minify)
  - highlight.js (logs)
  - Chart.js (metrics charts)

---

## 3) Core Data Contracts (Schemas First)
Before implementing logic, lock these schemas and validate them:
- `TaskSpec` (constraints, allowed tools, domain tags)
- `CandidateOutput` (+ optional tool traces)
- `Rubric` (weighted criteria, versioned)
- `ProbePlan` (bounded list of probes)
- `ProbeResult` (verdict, evidence, confidence, labels)
- `Decision` (A/R/C/E + rationale)
- `AuditTrace` (events timeline + timings + artifacts)

**Rule:** Every persisted record must be JSON-schema valid.

---

## 4) Agent Graph (LangGraph) — Standard Node Layout
Implement as an explicit state machine (no hidden loops):

1. `NormalizeInput`
2. `SelectRubric` (or generate-if-missing, but persist)
3. `GenerateProbePlan` (3–6 probes; cap 8)
4. `ExecuteProbes` (evidence-backed)
5. `ClassifyFailures` (taxonomy labels)
6. `DecideOutcome` (A/R/C/E)
7. `RevisionLoop` (optional, max 2)
8. `FinalizeTrace` (persist + report)

Guardrails:
- hard iteration cap
- per-probe timeout
- tool allowlist enforcement
- structured outputs only

---

## 5) Minimum Probe Suite (MVP)
Required probes:
- Instruction Compliance
- Claim Support / Grounding (context-only for MVP)
- Consistency (internal contradictions, totals, references)
- Schema/Contract Validation (JSON schema)
- Safety/Policy (rubric/constitution-driven checks)

Stretch probes (high-signal):
- Tool-trace verifier (tool misuse / hallucinated tool calls / arg validation)
- Counterexample probe generator (small adversarial tests)
- Calibration probe (uncertainty alignment)

---

## 6) How Claude Should Work on This Repo (Best Practices)
### 6.1 Token discipline (always)
Before proposing changes, request only:
- file paths + 20–60 relevant lines
- schema definitions involved
- exact error output (one stack trace, one failing test)
Avoid:
- whole files
- giant traces
- DB dumps

### 6.2 Maintain a short “Context Snapshot”
Keep a rolling snapshot under 200 tokens:
- Goal:
- Current state:
- Constraints:
- Files touched:
- Test plan:

### 6.3 Make changes PR-sized
Default scope per iteration:
- 1–3 files, plus tests
- no broad refactors unless explicitly requested

### 6.4 Prefer patch-style edits
When editing, output:
1) plan (max 6 bullets)
2) file-by-file patch notes
3) how to verify (exact commands)

### 6.5 Don’t reprint unchanged code
Reference by:
- file path
- function/class name
- line range (or snippet only)

---

## 7) Efficiency Rules for LLM Calls (Project-Specific)
### 7.1 Hard budgets
- max probes: 8
- max revise iterations: 2
- max tool calls per probe: define a cap (start at 2–3)
- global run timeout: define (e.g., 60–120s MVP)

### 7.2 Prefer smaller judges for cheap checks
If you support multiple models, use:
- cheap model for rubric compliance / schema checks
- stronger model only for hard classification or synthesis

### 7.3 Cache aggressively
Cache by hash of:
- (task_id, rubric_version, probe_suite_version, candidate_output_hash)
Store:
- ProbePlan cache
- ProbeResult cache (if deterministic)

### 7.4 Always require evidence for REVISE
Each REVISE iteration must include at least one:
- schema validation
- retrieval check
- sandbox/test execution
- tool-trace check

No “pure reflection” loops.

---

## Repo Layout

please reference the project named "punk-app" in the /Downloads folder on my computer. This has a great folder, project, and code structure to follow for this project especially for the UI and parts of the server or backend

## Design Suggestion
This is a very professional project the frontend should embody that. I want the scheme to be dark mode or black with white accents logos text etc.

---

## 9) UI Implementation Rules (Vanilla)
- Favor **server-rendered pages** with optional JS enhancements
- Filters should work via query params (no SPA requirement)
- Use Handlebars for repeated components:
  - probe cards
  - evidence blocks
  - run rows

Performance:
- paginate `/runs`
- lazy expand probe evidence
- use ETags on trace endpoints if possible

---

## 10) Default Commands (Adjust to Repo)
When giving run instructions, prefer:

- `uv sync`
- `docker compose up -d postgres redis`
- `uv run pytest -q`
- `uv run python -m apps.worker.run_one --task data/tasks/example.json`

If these don’t exist, ask for the repo’s `Makefile` or `README` commands.

---

## 11) Definition of Done (Project Standard)
A change is “done” when:
- tests pass (or you add first test for the new behavior)
- schemas validate (Pydantic + JSON schema)
- audit trace remains structured and replayable
- run output includes ProbePlan, ProbeResults, Decision, and AuditTrace
- no secrets are logged
- UI still renders runs/detail without breaking

---

## 12) When Requirements Conflict
Prioritize:
**auditability > determinism > safety > efficiency > features**

If a tradeoff is unavoidable:
- propose 2 options with pros/cons (max 6 bullets)
- request the smallest clarification possible

---

## 13) Compact Context Snapshot Template (Use This)
**Snapshot**
- Goal:
- Current state:
- Constraints:
- Files touched:
- Test plan:

Keep it short.


