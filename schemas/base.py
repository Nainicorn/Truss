"""Base schema definitions and utilities for Polaris."""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base Pydantic v2 model with strict validation."""

    model_config = ConfigDict(
        strict=False,
        frozen=False,
        extra="forbid",
        use_enum_values=False,
    )


class DecisionVerdict(str, Enum):
    """Decision verdicts for evaluation outcomes."""

    ACCEPT = "ACCEPT"
    REVISE = "REVISE"
    CONSTRAIN = "CONSTRAIN"
    ESCALATE = "ESCALATE"


class ProbeVerdict(str, Enum):
    """Probe execution verdicts."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"
    ERROR = "ERROR"


class NodeStatus(str, Enum):
    """Status of a node in the evaluation pipeline."""

    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FailureLabel(str, Enum):
    """Taxonomy of failure categories."""

    INSTRUCTION_VIOLATION = "INSTRUCTION_VIOLATION"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    INCONSISTENCY = "INCONSISTENCY"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    TOOL_MISUSE = "TOOL_MISUSE"
    HALLUCINATION = "HALLUCINATION"
    SAFETY_CONCERN = "SAFETY_CONCERN"
    OTHER = "OTHER"


class EvidenceSource(str, Enum):
    """Source types for probe evidence."""

    TEXT_SPAN = "TEXT_SPAN"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    SCHEMA_VALIDATION = "SCHEMA_VALIDATION"
    CONSISTENCY_CHECK = "CONSISTENCY_CHECK"
    OTHER = "OTHER"


def utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def generate_id(prefix: str) -> str:
    """Generate a unique ID with given prefix."""
    return f"{prefix}_{uuid4().hex[:12]}"
