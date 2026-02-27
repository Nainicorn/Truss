from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScanResult:
    injection_detected: bool
    confidence: float
    matched_patterns: list[str]
    highest_pattern: str

    def to_dict(self) -> dict:
        return {
            "injection_detected": self.injection_detected,
            "confidence": self.confidence,
            "matched_patterns": self.matched_patterns,
            "highest_pattern": self.highest_pattern,
        }


PATTERNS: list[dict] = [
    {
        "name": "instruction_override",
        "phrases": [
            "ignore previous instructions",
            "disregard your",
            "forget your instructions",
        ],
        "weight": 0.95,
    },
    {
        "name": "role_reassignment",
        "phrases": [
            "you are now",
            "act as",
            "your real instructions",
        ],
        "weight": 0.90,
    },
    {
        "name": "urgency_injection",
        "phrases": [
            "urgent:",
            "system override",
            "before doing anything else",
        ],
        "weight": 0.85,
    },
    {
        "name": "source_spoofing",
        "phrases": [
            "this is your operator",
            "new system prompt",
            "updated directive",
        ],
        "weight": 0.92,
    },
    {
        "name": "context_boundary",
        "phrases": [
            "---begin instructions---",
            "###system###",
            "<instructions>",
        ],
        "weight": 0.88,
    },
]

DETECTION_THRESHOLD = 0.85
AMBIGUOUS_THRESHOLD = 0.5


class InjectionScanner:
    def __init__(self) -> None:
        self._patterns = PATTERNS

    def scan(self, context: str) -> ScanResult:
        if not context or not context.strip():
            return ScanResult(
                injection_detected=False,
                confidence=0.0,
                matched_patterns=[],
                highest_pattern="",
            )

        text_lower = context.lower()
        matched: list[tuple[str, float]] = []

        for pattern in self._patterns:
            for phrase in pattern["phrases"]:
                if phrase.lower() in text_lower:
                    matched.append((pattern["name"], pattern["weight"]))
                    break  # one match per pattern is enough

        if not matched:
            return ScanResult(
                injection_detected=False,
                confidence=0.0,
                matched_patterns=[],
                highest_pattern="",
            )

        confidence = max(w for _, w in matched)
        highest = max(matched, key=lambda x: x[1])

        return ScanResult(
            injection_detected=confidence >= DETECTION_THRESHOLD,
            confidence=confidence,
            matched_patterns=[name for name, _ in matched],
            highest_pattern=highest[0],
        )
