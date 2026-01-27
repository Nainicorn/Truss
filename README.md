# Polaris 🌟
**Trace-based Evaluation, Governance, and Self-Correction Framework**

Polaris is a production-grade evaluation system that automatically tests AI model outputs against constraints and rubrics. It generates intelligent test probes, executes them with evidence collection, and produces transparent, auditable decisions with full execution traces.

---

## Why Polaris?

### The Problem
When evaluating AI model outputs, you need:
- **Transparency**: Why was this output accepted/rejected?
- **Reproducibility**: Run the same evaluation again and get the same result
- **Auditability**: Complete record of how the decision was made
- **Scalability**: Test multiple outputs against complex rubrics

### The Solution
Polaris provides:
✅ **Intelligent test probes** that understand constraints (not just keyword matching)
✅ **Evidence-backed decisions** with specific excerpts and reasoning
✅ **Immutable audit traces** for compliance and debugging
✅ **Web UI + REST API** for integration into any pipeline

## Key Features

### Intelligent Constraint Parsing
Not just keyword matching — Polaris understands:
- **Word count limits**: "100 words max" → counts actual words
- **Length constraints**: "under 500 characters" → validates length
- **Minimum requirements**: "at least 10 sentences" → enforces minimums
- **Semantic rules**: Falls back to keyword matching for complex constraints

### Evidence-Driven Decisions
Every decision includes:
- **Verdict**: ACCEPT, REVISE, CONSTRAIN, or ESCALATE
- **Rationale**: Why the decision was made
- **Evidence**: Specific excerpts or findings
- **Failed Probes**: Which tests failed and why
- **Confidence Scores**: How confident is this decision?

### Audit Trails & Reproducibility
- **Complete execution timeline**: Every step of the evaluation
- **Node timings**: See where time is spent
- **Tool call logs**: Track all function calls (when enabled)
- **Deterministic execution**: Run twice, get same result
- **JSONB storage**: Full run records searchable and queryable

---

## Quick Start

### Prerequisites
- **Docker & Docker Compose** (for PostgreSQL and Redis)
- **Python 3.11+** with `uv` package manager
- Git (optional, for cloning)

### 1. Start Infrastructure

```bash
# Start PostgreSQL and Redis containers
docker compose up -d postgres redis

# Verify containers are running
docker compose ps
```

### 2. Install Dependencies & Sync Environment

```bash
# Install Python dependencies
uv sync
```

### 3. Start the Server

In one terminal:
```bash
# Start FastAPI server on http://localhost:8000
uv run python -m server.main
```

You should see:
```
INFO:     Application startup complete.
```

### 4. Start the Worker

In another terminal:
```bash
# Start RQ worker listening on the 'polaris' queue
uv run rq worker -u redis://localhost:6379 polaris
```

You should see:
```
*** Listening on polaris...
```

### 5. Access the UI

Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

### Create & Monitor Runs via Web UI

1. Navigate to the **"Evaluation Runs"** page at `/runs`
2. Click **"Show Form"** to expand the run creation form
3. Fill in the evaluation details:
   - **Task ID**: Unique identifier for the task (e.g., `task_001`)
   - **Candidate ID**: Model or agent identifier (e.g., `gpt-4-v1`)
   - **Task Description**: What the candidate needs to do
   - **Candidate Output**: The response/output to evaluate
   - **Constraints** (optional): Rules the output must satisfy (comma-separated)
4. Click **"Create Run"**
5. The page auto-refreshes every 5 seconds while the run is processing
6. Once **COMPLETED**, click the run ID to view detailed results

### View Results

Each completed run shows:
- **Verdict**: ACCEPT, REVISE, CONSTRAIN, or ESCALATE
- **Probe Results**: Detailed findings from each test
- **Evidence**: Specific excerpts or findings supporting each decision
- **Audit Trace**: Complete timeline of evaluation steps

### Create Runs via API

```bash
curl -X POST http://localhost:8000/api/runs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{
    "task_spec": {
      "task_id": "task_001",
      "description": "Evaluate the response quality",
      "constraints": ["Must be under 500 words"],
      "domain_tags": ["test"]
    },
    "candidate_output": {
      "candidate_id": "my_model_v1",
      "content": "The response to evaluate",
      "tool_calls": []
    }
  }'
```

## Architecture

### Tech Stack
| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, Pydantic v2 |
| **Database** | PostgreSQL 16 (JSONB for flexible schema) |
| **Job Queue** | Redis + RQ (Redis Queue) for async evaluation |
| **Orchestration** | LangGraph (state machine for evaluation pipeline) |
| **UI** | Vanilla JS (ES2022), HTML5, Handlebars, CSS (no frameworks) |
| **DevOps** | Docker, Docker Compose |

**Why these choices?**
- **FastAPI**: Type-safe, auto-docs (OpenAPI), async support
- **Pydantic v2**: Schema validation, JSON serialization for audit trails
- **PostgreSQL JSONB**: Flexible schema for complex run records while maintaining ACID guarantees
- **LangGraph**: Explicit state machine prevents hidden loops and ensures reproducibility
- **Vanilla JS**: Zero dependencies, lightweight polling logic, minimal build pipeline

### Core Flow

```
1. Create Run
   ├─ Validate task_spec & candidate_output
   ├─ Store in database with QUEUED status
   └─ Enqueue job to Redis

2. RQ Worker
   ├─ Pick up job from queue
   ├─ Update status to RUNNING
   ├─ Execute LangGraph evaluation graph
   │  ├─ Normalize inputs
   │  ├─ Generate probe plan (3 probes)
   │  ├─ Execute probes with evidence
   │  ├─ Classify failures (taxonomy labels)
   │  └─ Produce decision (A/R/C/E)
   └─ Store run_record, set status COMPLETED

3. View Results
   ├─ Fetch run from database
   ├─ Display audit trace, probe results
   └─ Download markdown report (optional)
```

### Probe Suite (MVP)

Every run executes 3 deterministic probes:

1. **Instruction Compliance** (`instruction_compliance.py`)
   - ✨ Smart constraint validation (word count, length, minimums)
   - Regex parsing for numeric constraints
   - Fallback keyword matching for semantic rules
   - Returns: PASS/FAIL with evidence

2. **Schema Validation** (`schema_validation.py`)
   - Validates output structure and required fields
   - JSON round-trip validation (serialize → deserialize → validate)
   - Checks for malformed or incomplete responses
   - Returns: PASS/FAIL with specific field errors

3. **Consistency Check** (`consistency_check.py`)
   - Detects contradictions (yes/no, true/false, etc.)
   - Warns on excessive length (>100k chars)
   - Checks for empty content
   - Returns: PASS/FAIL with contradiction details

**Deterministic & Fast**: All probes run synchronously with no LLM calls (MVP) — results are reproducible and instant.

## Environment Variables

Create a `.env` file in the project root (optional — uses defaults if not present):

```bash
# Database
DATABASE_URL="postgresql://polaris:polaris@localhost:5432/polaris"

# Redis
REDIS_URL="redis://localhost:6379/0"

# API
API_KEYS="dev-key-12345"  # Comma-separated for production
RATE_LIMIT_PER_MINUTE=10

# Worker
RQ_QUEUE_NAME="polaris"
```

## Running Tests

```bash
# Run all tests
uv run pytest -q

# Run specific test file
uv run pytest tests/test_ui.py -v
```

## Stopping Services

```bash
# Stop server (Ctrl+C in terminal)
# Stop worker (Ctrl+C in terminal)

# Stop Docker containers
docker compose down

# Remove volumes (careful: deletes data)
docker compose down -v
```

## Project Structure

```
polaris/
├── config/              # Configuration & settings
├── db/                  # Database layer (repositories, migrations)
├── schemas/             # Pydantic models (TaskSpec, CandidateOutput, RunRecord, etc.)
├── graphs/              # LangGraph evaluation pipeline
├── probes/              # Probe implementations (Instruction, Claim, Consistency, etc.)
├── server/              # FastAPI application & routes
│  ├── main.py          # Server entry point
│  ├── worker.py        # RQ worker for running evaluations
│  └── routes/          # API endpoints (runs, metrics, etc.)
├── ui/                  # Web interface
│  ├── templates/       # Jinja2 HTML templates
│  └── static/          # CSS, JavaScript, assets
├── tests/               # Test suites
├── docker-compose.yml  # PostgreSQL + Redis setup
└── pyproject.toml      # Python dependencies
```

## Troubleshooting

### Server won't start on port 8000
```bash
# Check what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uv run python -m server.main --port 8001
```

### Worker not processing jobs
```bash
# Verify worker is listening on correct queue name
# Check config/settings.py: rq_queue_name should be "polaris"

# Verify Redis is running
redis-cli ping  # Should return PONG

# Check worker logs for errors (should show "*** Listening on polaris...")
```

### Database connection errors
```bash
# Verify PostgreSQL is running
docker compose ps | grep postgres

# Check database exists
psql postgresql://polaris:polaris@localhost:5432/polaris -c "SELECT 1"

# Restart database
docker compose down postgres
docker compose up -d postgres
```

## Development Notes

- **Schemas are locked** in Phase 1 — changes require careful consideration
- **Audit trail is immutable** — all decisions are permanently recorded
- **Probe execution is capped at 3** per run (MVP) — extensible in future phases
- **Strict validation** — invalid task_spec or candidate_output rejected at API boundary

## Roadmap

### Phase 5 (In Progress)
- Add support for **revision loops** (max 2 iterations) — allow outputs to be improved automatically
- Implement **failure taxonomy dashboard** — categorize failure patterns
- Add **metrics & analytics** page — track evaluation trends

### Phase 6+ (Future)
- **Custom rubrics** — define domain-specific evaluation rules
- **Tool-call verification** — validate function calls and arguments
- **LLM-powered probes** — use language models for semantic evaluation
- **Failure prediction** — predict which outputs will fail before running
- **Batch evaluation** — process 1000s of outputs efficiently

---

## Contributing

This project follows strict architectural principles (see [CLAUDE.md](CLAUDE.md)):
- Schemas must be locked before implementation
- All decisions must be auditable and reproducible
- No unbounded loops (max 2 iterations for revisions)
- Tests required for new probe implementations

## License

See LICENSE file for details.

---

**Questions or feedback?** Open an issue on GitHub or review the [CLAUDE.md](CLAUDE.md) file for architectural details and development guidelines.
