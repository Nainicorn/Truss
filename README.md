# Helm — Verification-First AgentOps Platform

Helm is a platform for running and verifying autonomous AI workflows. It enables AI agents to plan and execute real-world tasks using tools (browser automation, document parsing, APIs) — and then **proves they actually worked** through evidence-backed verification and full audit trails.

Most agent systems report success with no proof. Helm verifies it.

<!-- TODO: Add demo screenshot or GIF here -->

---

## The Problem

Current AI agents "complete" tasks, but they:

- Hallucinate success with no proof of execution
- Provide no evidence trail for what actually happened
- Can't distinguish between "I tried" and "I confirmed it worked"
- Are impossible to audit, debug, or safely reuse

Helm treats AI agents like production systems, not chatbots. Every action is planned, executed, **verified with evidence**, and replayable.

---

## Core Differentiator: Verification-First Design

Instead of trusting agent output, every step is verified using an **LLM-as-judge approach**: step outputs and captured evidence (screenshots, text extracts) are passed to a vision-capable model, which returns a structured verdict with a confidence score, reasoning, and citations.

This enables verification of steps that can't be checked with simple pattern matching — like confirming extracted data matches what was requested, or that a document actually contains the expected content.

Each verification produces a confidence score:
- **≥ 0.9** → auto-verified
- **0.7–0.9** → verified with warning
- **< 0.7** → flagged for review

Every step captures evidence regardless of outcome — failures are documented too.

---

## Demo: Automated Compliance Checking

The flagship demo is **automated compliance checking against a document** — verifiable pass/fail with citations.

### How It Works

1. **User submits**: "Check our privacy policy against GDPR Article 13 requirements"
2. **Planner** breaks this into steps: extract requirements, parse policy, check each requirement, compile report
3. **Executor** runs tools: document parsing, text extraction, requirement matching
4. **Verifier** confirms each check — LLM-judge compares extracted text against each requirement, produces pass/fail with evidence citations
5. **Evidence captured**: source text snippets, requirement-to-policy mapping, confidence scores
6. **Report generated**: per-requirement compliance status with evidence links and audit trail

### Why This Use Case

- Verification is unambiguous — requirement is met or not, with cited evidence
- Output has clear business value — compliance reports are real work product
- Showcases every layer: planning, tool use, verification, evidence, audit trail
- Not fragile against anti-bot detection (works on local documents)

---

## Architecture

```
                    ┌─────────┐
                    │ Planner │  ← LLM breaks task into steps
                    └────┬────┘
                         │
                    ┌────▼─────┐
                    │ Executor │  ← runs tools (browser, file parser, API)
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ Verifier │  ← LLM-as-judge with evidence
                    └────┬─────┘
                         │
                    ┌────▼────┐
               ┌────│ Router  │────┐
               │    └─────────┘    │
          more steps          all done
               │                   │
               ▼                   ▼
          [Executor]         ┌──────────┐
                             │ Reporter │  ← evidence report + audit trail
                             └──────────┘
```

The orchestrator is a simple async Python loop — no framework overhead. WebSocket streaming pushes real-time execution events to the frontend.

### Run Status State Machine

```
pending → planning → executing → verifying → completed
                                           ↘ failed
                          (any state) ────→ cancelled
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Vanilla JS (ES6 modules), CSS, Vite |
| **Backend** | Python 3.12+, FastAPI, SQLModel, WebSockets |
| **Browser Automation** | playwright-python (in-process) |
| **Storage** | SQLite (MVP), local filesystem for evidence |
| **AI** | Anthropic Claude (planning + LLM-judge verification) |

---

## Data Model

```
Task          → top-level user request
├── Run       → single execution attempt (with explicit status state machine)
│   ├── Step  → individual action ("Extract GDPR Art. 13 requirements")
│   │   └── Evidence  → proof artifacts (screenshots, text extracts, logs)
│   └── Event → streaming execution events (for real-time UI)
```

Each step tracks `duration_ms` and `estimated_cost_usd` — because production awareness matters.

---

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.12+

### Setup

```bash
git clone https://github.com/nainicorn/helm.git
cd helm
```

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload    # localhost:8000
```

#### Frontend

```bash
npm install
npm run dev                      # localhost:5173
```

---

## Roadmap

### Current (MVP)
- Async orchestrator with plan → execute → verify loop
- LLM-as-judge verification with confidence scoring
- Evidence capture on every step (including failures)
- WebSocket-powered live run viewer
- Compliance checking demo with fixtures

### Next
- LangGraph migration for state checkpointing + crash recovery
- PostgreSQL + Supabase for production persistence
- Multiple verification strategies (text match, schema validation)
- Human-in-the-loop approval gate for low-confidence verifications
- Evaluation harness with YAML-defined test suites

---

## Author

Built by **Sreenaina Koujala**

- Website: [sreenaina.com](https://sreenaina.com)
- LinkedIn: [linkedin.com/in/sreenaina-koujala-a65821192](https://linkedin.com/in/sreenaina-koujala-a65821192)
- X: [@nains_k](https://x.com/nains_k)

---

## License

MIT License