# Demo Agent

Deliberately dangerous agent for demonstrating Truss safety middleware.

## Running Scenarios

```bash
# Start backend first
cd backend && uvicorn app.main:app --reload

# Email injection — without/with Truss
python -m demo_agent.scenarios.email_injection --truss=false
python -m demo_agent.scenarios.email_injection --truss=true

# File exfiltration — without/with Truss
python -m demo_agent.scenarios.file_exfiltration --truss=false
python -m demo_agent.scenarios.file_exfiltration --truss=true
```

## Architecture

- `tools.py` — Simulated tools (delete_files, send_email, exec_command). They log what *would* happen but don't actually execute. Each tool maps to a Truss action via `TOOL_REGISTRY`.
- `agent.py` — `DemoAgent` class. Reads `TRUSS_ENABLED` env var. When true, calls `POST /api/gate` via the Python SDK before every tool execution.
- `scenarios/` — Self-contained attack scripts. Each defines a malicious context and a sequence of tool calls.

## Key Behaviors

| Mode | What happens |
|------|-------------|
| `TRUSS_ENABLED=false` | Agent executes every tool call. No checks. |
| `TRUSS_ENABLED=true` | Every call routes through Truss. Injection → block. Critical blast → block. High/medium → escalate. |
| Server unreachable | Agent aborts action (fail-safe). |
