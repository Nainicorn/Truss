"""Demo agent that executes dangerous tools.

When TRUSS_ENABLED=false (default for demo), the agent executes every tool
call without any safety checks — showing what happens without Truss.

When TRUSS_ENABLED=true, every tool call is routed through the Truss gate
API before execution. Blocked actions are aborted. Escalated actions pause.
"""
from __future__ import annotations

import os
import sys

from demo_agent.tools import TOOL_REGISTRY, ToolResult


class AgentLog:
    """Collects agent activity for display."""

    def __init__(self):
        self.entries: list[str] = []

    def log(self, message: str) -> None:
        self.entries.append(message)
        print(message)

    def dump(self) -> str:
        return "\n".join(self.entries)


class DemoAgent:
    """A deliberately dangerous agent for demonstrating Truss.

    Args:
        truss_enabled: Override TRUSS_ENABLED env var. If None, reads from env.
        truss_url: Base URL for the Truss server.
        agent_id: Identifier for this agent instance.
    """

    def __init__(
        self,
        truss_enabled: bool | None = None,
        truss_url: str = "http://localhost:8000",
        agent_id: str = "demo-agent",
    ):
        if truss_enabled is not None:
            self.truss_enabled = truss_enabled
        else:
            self.truss_enabled = os.environ.get("TRUSS_ENABLED", "false").lower() == "true"

        self.truss_url = truss_url
        self.agent_id = agent_id
        self.session_id: str | None = None
        self.log = AgentLog()
        self._truss = None

    def _get_truss(self):
        """Lazy-load the Truss SDK client."""
        if self._truss is None:
            # Import here so the SDK is only needed when Truss is enabled
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from sdk.python.truss_sdk import Truss
            self._truss = Truss(base_url=self.truss_url, session_id=self.session_id)
        return self._truss

    def start_session(self) -> None:
        """Register a session with Truss (only when enabled)."""
        if self.truss_enabled:
            truss = self._get_truss()
            session = truss.create_session(agent_id=self.agent_id)
            self.session_id = session["id"]
            truss.session_id = self.session_id
            self.log.log(f"[TRUSS] Session registered: {self.session_id}")
        else:
            self.log.log("[AGENT] Running WITHOUT safety checks (TRUSS_ENABLED=false)")

    def execute(self, tool_name: str, params: dict, context: str = "") -> ToolResult | None:
        """Execute a tool, optionally routing through Truss first.

        Returns:
            ToolResult if execution proceeded, None if blocked by Truss.
        """
        if tool_name not in TOOL_REGISTRY:
            self.log.log(f"[AGENT] Unknown tool: {tool_name}")
            return None

        entry = TOOL_REGISTRY[tool_name]
        fn = entry["fn"]
        truss_action = entry["truss_action"]

        self.log.log(f"\n[AGENT] Tool call: {tool_name}({params})")
        if context:
            self.log.log(f"[AGENT] Context: {context[:120]}{'...' if len(context) > 120 else ''}")

        # --- Truss gate check ---
        if self.truss_enabled:
            decision = self._check_gate(truss_action, params, context)
            if decision is None:
                # Gate unreachable — fail safe
                self.log.log("[TRUSS] Gate unreachable — aborting action (fail-safe)")
                return None
            if decision.is_blocked:
                self.log.log(f"[TRUSS] BLOCKED — {decision.reason}")
                self.log.log(f"[TRUSS]   blast_radius={decision.blast_radius}, confidence={decision.confidence}")
                return None
            if decision.is_escalated:
                self.log.log(f"[TRUSS] ESCALATED — {decision.reason}")
                self.log.log(f"[TRUSS]   blast_radius={decision.blast_radius}, confidence={decision.confidence}")
                self.log.log("[TRUSS]   Waiting for human approval... (auto-skipping for demo)")
                # In a real agent, this would pause and wait. For demo, we skip.
                return None
            # Approved
            self.log.log(f"[TRUSS] APPROVED — {decision.reason}")

        # --- Execute the tool ---
        result = fn(**params)
        self.log.log(f"[AGENT] Result: {result}")
        return result

    def _check_gate(self, action: str, params: dict, context: str):
        """Call Truss gate API. Returns GateDecision or None on connection failure."""
        try:
            truss = self._get_truss()
            return truss.gate(action=action, params=params, context=context)
        except ConnectionError:
            return None

    def run_scenario(self, steps: list[dict]) -> None:
        """Run a sequence of tool calls (a scenario).

        Each step is a dict with keys: tool, params, context (optional).
        """
        self.log.log("=" * 60)
        mode = "WITH TRUSS" if self.truss_enabled else "WITHOUT TRUSS"
        self.log.log(f"  Demo Agent — Running {mode}")
        self.log.log("=" * 60)

        self.start_session()

        for i, step in enumerate(steps, 1):
            self.log.log(f"\n--- Step {i}/{len(steps)} ---")
            self.execute(
                tool_name=step["tool"],
                params=step["params"],
                context=step.get("context", ""),
            )

        self.log.log("\n" + "=" * 60)
        self.log.log("  Scenario complete.")
        self.log.log("=" * 60)
