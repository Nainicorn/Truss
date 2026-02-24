# Helm — AgentOps Platform

Helm is a production-oriented platform I built to run, verify, and govern autonomous AI workflows

It enables AI agents to plan and execute real-world tasks using tools
(browser automation, APIs, files, and code) AND also provides evidence-backed
verification, human oversight, and full audit trails

Helm focuses on making autonomous AI systems reliable, inspectable, and safe to use in real workflows

---

## Why Helm Exists

Current AI agents "try" to complete tasks, but they:

- Often hallucinate success
- Provide no proof of execution
- Are difficult to debug
- Cannot be safely reused
- Lack governance and auditability

Helm solves this by treating AI agents like production systems rather than chatbots

Every action is logged, verified, and replayable (full control plane access)

---

## Key Features

- Autonomous task planning and execution
- Tool-using agents (browser, APIs, files, code)
- Evidence-backed verification (screenshots, DOM snapshots, artifacts)
- Policy-based governance and permissions
- Human-in-the-loop approval
- Replayable execution traces
- Reusable workflow templates
- Real-time progress streaming
- Built-in evaluation and metrics

---

##  Example User Workflow

### Goal

Apply to 10 software engineering internships and save the results.

### Execution Flow

1. User submits a task and selects permissions
2. Helm generates a structured execution plan
3. Agent searches job boards
4. Agent checks eligibility requirements
5. Agent fills and submits applications
6. Screenshots and confirmations are captured
7. Results are verified
8. A report is generated

### Result

- Spreadsheet with submitted applications
- Evidence for each submission
- Full replayable timeline

---

##  Architecture Overview

Helm consists of four core components:

1. **Frontend UI** — dashboard, live runs, evidence viewer
2. **API Server** — planning, orchestration, streaming
3. **Tool Workers** — Playwright automation, file handlers
4. **Storage Layer** — database, cache, evidence store

All execution is event-driven and fully logged.

---

## Tech Stack

### Frontend
- Vanilla JavaScript (ES6 Modules)
- Handlebars (HBS)
- CSS
- Vite

### Backend
- Python
- FastAPI
- Pydantic
- SQLModel / SQLAlchemy
- WebSockets

### Workers
- Node.js
- Playwright

### Storage
- PostgreSQL (Supabase)
- Supabase Storage (evidence artifacts)
- Redis (Upstash)

### AI / Agents
- LangGraph
- OpenAI / Anthropic
- MCP-style tool registry

### Deployment
- AWS Amplify (Frontend)
- AWS App Runner (Backend)
- Docker Compose (Local Dev)

---

##  Repository Structure

```
helm/
├── frontend/
│   ├── src/
│   ├── templates/
│   ├── styles/
│   └── components/
├── backend/
│   ├── app/
│   ├── api/
│   ├── orchestrator/
│   ├── verifier/
│   └── models/
├── workers/
│   └── playwright/
├── infra/
│   └── docker/
└── docs/
```

---

## Verification & Governance

Helm enforces correctness through:

- Output schema validation
- Evidence requirements
- DOM and screenshot inspection
- Confirmation detection
- Policy enforcement
- Retry and escalation rules

If a step cannot be verified, it is not marked as complete

---

##  Human-in-the-Loop

Helm supports manual approval when needed

Users can:

- Review filled forms
- Inspect generated content
- Approve submissions
- Modify actions
- Add new rules

This enables safe deployment in sensitive workflows

---

##  Evaluation & Metrics

Helm includes automated evaluation pipelines that track:

- Success rate
- Failure causes
- Tool reliability
- Retry frequency
- Execution time

This enables continuous improvement of agent behavior

---

##  Local Development

### Prerequisites

- Docker
- Node.js 20+
- Python 3.12+

### Setup

```bash
git clone https://github.com/yourusername/helm.git
cd helm
docker compose up
```

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

##  Roadmap

- [ ] Template marketplace
- [ ] Advanced policy engine
- [ ] Multi-agent coordination
- [ ] Workflow versioning
- [ ] Plugin SDK
- [ ] Enterprise SSO
- [ ] Scheduled runs
- [ ] Distributed execution

---

##  Use Cases

- Job application automation
- Competitive research
- Compliance audits
- Data reconciliation
- Sales outreach
- Document processing
- System onboarding
- Price monitoring

---

##  Project Goals

Helm aims to:

- Make AI automation trustworthy
- Enable reproducible agent behavior
- Reduce operational risk
- Bridge research and production
- Establish best practices for AgentOps

---

## 👤 Author

Built by **Sreenaina Koujala**

-  Website: [sreenaina.com](https://sreenaina.com)
-  LinkedIn: [linkedin.com/in/sreenaina-koujala-a65821192](https://linkedin.com/in/sreenaina-koujala-a65821192)
-  X: [nains_k] (https://x.com/nains_k)

---

## 📄 License

MIT License