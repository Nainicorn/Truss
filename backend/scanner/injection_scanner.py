from __future__ import annotations

import re
import unicodedata
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


# Common homoglyph/confusable character mapping (Cyrillic, Greek → Latin)
_CONFUSABLES: dict[str, str] = {
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p",
    "\u0441": "c", "\u0443": "y", "\u0445": "x", "\u0456": "i",
    "\u0458": "j", "\u0455": "s", "\u044a": "b", "\u043a": "k",
    "\u0410": "A", "\u0415": "E", "\u041e": "O", "\u0420": "P",
    "\u0421": "C", "\u0423": "Y", "\u0425": "X", "\u041a": "K",
    "\u0392": "B", "\u0395": "E", "\u0396": "Z", "\u0397": "H",
    "\u039a": "K", "\u039c": "M", "\u039d": "N", "\u039f": "O",
    "\u03a1": "P", "\u03a4": "T", "\u03a5": "Y", "\u03a7": "X",
    "\u0131": "i",  # Turkish dotless i
    "\u0130": "I",  # Turkish capital I with dot
}


def _normalize_text(text: str) -> str:
    """Normalize text to defeat common evasion techniques."""
    # NFKD decomposition: converts fullwidth, compatibility chars to ASCII equivalents
    text = unicodedata.normalize("NFKD", text)
    # Replace confusable homoglyphs (Cyrillic/Greek lookalikes → Latin)
    text = "".join(_CONFUSABLES.get(ch, ch) for ch in text)
    # Strip zero-width and formatting characters (Unicode category Cf)
    # and control characters (Cc) except common whitespace
    text = "".join(
        ch for ch in text
        if unicodedata.category(ch) not in ("Cf", "Cc") or ch in ("\n", "\r", "\t")
    )
    # Strip combining marks (diacritics left over from NFKD decomposition)
    text = "".join(ch for ch in text if unicodedata.category(ch) not in ("Mn", "Mc", "Me"))
    # Collapse all whitespace (tabs, newlines, multiple spaces, NBSP) to single space
    text = re.sub(r"\s+", " ", text)
    # Casefold for aggressive Unicode-aware lowering (handles Turkish I, etc.)
    text = text.casefold()
    return text


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

        text_lower = _normalize_text(context)
        matched: list[tuple[str, float]] = []

        for pattern in self._patterns:
            for phrase in pattern["phrases"]:
                if phrase.casefold() in text_lower:
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
