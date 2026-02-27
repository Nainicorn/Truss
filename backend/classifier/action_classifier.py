from __future__ import annotations

from dataclasses import dataclass

from backend.classifier.taxonomy import TAXONOMY, ALIASES, ActionDef


@dataclass
class ClassificationResult:
    action_key: str
    category: str
    reversible: bool
    blast_radius: str
    description: str
    recognized: bool

    def to_dict(self) -> dict:
        return {
            "action_key": self.action_key,
            "category": self.category,
            "reversible": self.reversible,
            "blast_radius": self.blast_radius,
            "description": self.description,
            "recognized": self.recognized,
        }


# Default for unrecognized actions: treat as irreversible + high blast radius (fail safe)
_UNKNOWN = ActionDef(
    category="unknown",
    action="unknown",
    reversible=False,
    blast_radius="high",
    description="Unrecognized action — treated as high risk",
)


class ActionClassifier:
    def __init__(self) -> None:
        self._taxonomy = TAXONOMY
        self._aliases = ALIASES

    def classify(self, action: str, params: dict | None = None) -> ClassificationResult:
        resolved = self._resolve(action)
        action_def = self._taxonomy.get(resolved, _UNKNOWN)
        recognized = resolved in self._taxonomy

        return ClassificationResult(
            action_key=resolved if recognized else action,
            category=action_def.category,
            reversible=action_def.reversible,
            blast_radius=action_def.blast_radius,
            description=action_def.description,
            recognized=recognized,
        )

    def _resolve(self, action: str) -> str:
        normalized = action.strip().lower()
        if normalized in self._taxonomy:
            return normalized
        if normalized in self._aliases:
            return self._aliases[normalized]
        return normalized
