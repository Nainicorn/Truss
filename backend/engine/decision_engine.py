from __future__ import annotations

from dataclasses import dataclass

from backend.classifier.action_classifier import ActionClassifier, ClassificationResult
from backend.scanner.injection_scanner import InjectionScanner, ScanResult


@dataclass
class Decision:
    decision: str  # "approve" | "block" | "escalate"
    confidence: float
    blast_radius: str
    reversible: bool
    injection_detected: bool
    reason: str
    classification: ClassificationResult
    scan: ScanResult

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "confidence": self.confidence,
            "blast_radius": self.blast_radius,
            "reversible": self.reversible,
            "injection_detected": self.injection_detected,
            "reason": self.reason,
            "layer_results": {
                "classifier": self.classification.to_dict(),
                "scanner": self.scan.to_dict(),
            },
        }


class DecisionEngine:
    def __init__(self) -> None:
        self._classifier = ActionClassifier()
        self._scanner = InjectionScanner()

    def evaluate(self, action: str, params: dict | None = None, context: str = "") -> Decision:
        classification = self._classifier.classify(action, params)
        scan = self._scanner.scan(context)

        decision, reason = self._apply_rules(classification, scan)
        confidence = self._compute_confidence(classification, scan, decision)

        return Decision(
            decision=decision,
            confidence=confidence,
            blast_radius=classification.blast_radius,
            reversible=classification.reversible,
            injection_detected=scan.injection_detected,
            reason=reason,
            classification=classification,
            scan=scan,
        )

    def _apply_rules(self, c: ClassificationResult, s: ScanResult) -> tuple[str, str]:
        # Rule 1: injection detected with high confidence → block
        if s.injection_detected and s.confidence >= 0.85:
            return "block", (
                f"Injection detected ({s.highest_pattern}) with confidence {s.confidence:.2f}"
            )

        # Rule 2: critical blast radius → block
        if c.blast_radius == "critical":
            return "block", (
                f"Action '{c.action_key}' has critical blast radius — blocked by policy"
            )

        # Rule 3: irreversible + high blast radius → escalate
        if not c.reversible and c.blast_radius == "high":
            return "escalate", (
                f"Action '{c.action_key}' is irreversible with high blast radius — requires approval"
            )

        # Rule 4: irreversible + medium blast radius → escalate (with timeout)
        if not c.reversible and c.blast_radius == "medium":
            return "escalate", (
                f"Action '{c.action_key}' is irreversible with medium blast radius — requires approval (timeout applies)"
            )

        # Rule 5: ambiguous injection (0.5-0.85) → escalate for review
        if s.confidence >= 0.5 and not s.injection_detected:
            return "escalate", (
                f"Ambiguous injection signal ({s.highest_pattern}) with confidence {s.confidence:.2f} — needs review"
            )

        # Default: approve
        return "approve", "Action permitted — low risk, no injection detected"

    def _compute_confidence(self, c: ClassificationResult, s: ScanResult, decision: str) -> float:
        if decision == "block":
            if s.injection_detected:
                return s.confidence
            # Critical blast radius block — full confidence from taxonomy
            return 1.0

        if decision == "escalate":
            if s.confidence >= 0.5:
                return s.confidence
            # Escalation from blast radius rules
            return 0.9

        # Approve — high confidence when action is recognized
        if c.recognized:
            return 1.0 - s.confidence if s.confidence > 0 else 1.0
        return 0.8  # unrecognized but no injection signal
