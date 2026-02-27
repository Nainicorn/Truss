from __future__ import annotations

import hashlib
import hmac
import json

from backend.app.config import settings
from backend.models.gate import AuditEntry, GateRequest, GateDecision


def _build_payload(request: GateRequest, decision: GateDecision) -> str:
    """Build a canonical JSON payload for HMAC signing."""
    data = {
        "request_id": request.id,
        "decision_id": decision.id,
        "action": request.action,
        "decision": decision.decision,
        "confidence": decision.confidence,
        "blast_radius": decision.blast_radius,
        "injection_detected": decision.injection_detected,
        "decided_at": decision.decided_at,
    }
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def sign(request: GateRequest, decision: GateDecision) -> str:
    """Generate an HMAC-SHA256 signature for a gate decision."""
    payload = _build_payload(request, decision)
    return hmac.new(
        settings.HMAC_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify(entry: AuditEntry, request: GateRequest, decision: GateDecision) -> bool:
    """Verify an audit entry's HMAC signature."""
    expected = sign(request, decision)
    return hmac.compare_digest(entry.signature, expected)


def create_audit_entry(request: GateRequest, decision: GateDecision) -> AuditEntry:
    """Create a signed audit entry for a gate request/decision pair."""
    signature = sign(request, decision)
    return AuditEntry(
        signature=signature,
        request_id=request.id,
        decision_id=decision.id,
    )
