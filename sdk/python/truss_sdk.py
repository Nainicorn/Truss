"""Truss Python SDK — thin client for the Truss Gate API."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


@dataclass
class GateDecision:
    """Result of a gate check."""
    decision: str  # "approve" | "block" | "escalate"
    confidence: float
    blast_radius: str
    reversible: bool
    injection_detected: bool
    reason: str
    request_id: str
    decision_id: str
    audit_id: str
    layer_results: dict

    @property
    def is_allowed(self) -> bool:
        return self.decision == "approve"

    @property
    def is_blocked(self) -> bool:
        return self.decision == "block"

    @property
    def is_escalated(self) -> bool:
        return self.decision == "escalate"


class TrussError(Exception):
    """Raised when the Truss API returns an error."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Truss API error ({status_code}): {detail}")


class Truss:
    """Client for the Truss agent safety middleware.

    Usage:
        truss = Truss()
        decision = truss.gate("filesystem.delete", params={"path": "/tmp/data"})
        if decision.is_allowed:
            # proceed with action
        elif decision.is_blocked:
            # abort
        elif decision.is_escalated:
            # wait for approval
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        session_id: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id
        self.timeout = timeout

    def gate(
        self,
        action: str,
        params: Optional[dict[str, Any]] = None,
        context: str = "",
        session_id: Optional[str] = None,
    ) -> GateDecision:
        """Check an action through the Truss safety gate.

        Args:
            action: The action to check (e.g., "filesystem.delete", "shell.exec").
            params: Action parameters.
            context: Context string (checked for injection).
            session_id: Override the default session_id for this request.

        Returns:
            GateDecision with the verdict.

        Raises:
            TrussError: If the API returns a non-200 response.
            ConnectionError: If the Truss server is unreachable.
        """
        payload = {
            "action": action,
            "params": params or {},
            "context": context,
            "session_id": session_id or self.session_id or "",
        }

        data = self._post("/api/gate", payload)

        return GateDecision(
            decision=data["decision"],
            confidence=data["confidence"],
            blast_radius=data["blast_radius"],
            reversible=data["reversible"],
            injection_detected=data["injection_detected"],
            reason=data["reason"],
            request_id=data["request_id"],
            decision_id=data["decision_id"],
            audit_id=data["audit_id"],
            layer_results=data.get("layer_results", {}),
        )

    def create_session(
        self,
        agent_id: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict:
        """Register a new session with the Truss server.

        Returns:
            The session dict with id, agent_id, created_at, metadata.
        """
        data = self._post("/api/sessions", {
            "agent_id": agent_id,
            "metadata": metadata or {},
        })
        return data["session"]

    def health(self) -> dict:
        """Check the Truss server health."""
        return self._get("/api/health")

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode()
        req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        return self._send(req)

    def _get(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        req = Request(url, method="GET")
        return self._send(req)

    def _send(self, req: Request) -> dict:
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            body = e.read().decode()
            try:
                detail = json.loads(body).get("detail", body)
            except (json.JSONDecodeError, AttributeError):
                detail = body
            raise TrussError(e.code, detail)
        except URLError as e:
            raise ConnectionError(f"Cannot reach Truss server at {self.base_url}: {e.reason}")
