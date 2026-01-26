"""Probe-related schemas for evaluation."""

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from schemas.base import (
    BaseSchema,
    EvidenceSource,
    FailureLabel,
    ProbeVerdict,
    utc_now,
)


class ProbeDefinition(BaseSchema):
    """Definition of a single probe to execute."""

    probe_id: str = Field(..., description="Unique probe identifier")
    probe_type: str = Field(
        ...,
        description="Type of probe (e.g., 'instruction_compliance', 'schema_validation')",
    )
    description: str = Field(..., description="Human-readable probe description")
    rationale: str = Field(..., description="Why this probe is being run")
    expected_checks: list[str] = Field(
        default_factory=list, description="Checklist items for this probe"
    )


class ProbePlan(BaseSchema):
    """Plan specifying which probes to execute on a candidate output."""

    version: str = Field(default="1.0.0", description="Schema version")
    plan_id: str = Field(..., description="Unique plan identifier")
    task_id: str = Field(..., description="Reference to parent task")
    candidate_id: str = Field(..., description="Reference to candidate output")
    probes: list[ProbeDefinition] = Field(
        ..., description="Ordered list of probes to execute (max 8)"
    )
    created_at: datetime = Field(
        default_factory=utc_now, description="When plan was created"
    )

    @field_validator("probes")
    @classmethod
    def validate_probe_count(cls, v: list[ProbeDefinition]) -> list[ProbeDefinition]:
        """Enforce max 8 probes and min 1 probe."""
        if len(v) == 0:
            raise ValueError("At least 1 probe required")
        if len(v) > 8:
            raise ValueError(f"Maximum 8 probes allowed, got {len(v)}")
        return v


class Evidence(BaseSchema):
    """Evidence supporting a probe result."""

    source: EvidenceSource = Field(
        ..., description="Type of evidence (enum, not free text)"
    )
    excerpt: str | None = Field(
        default=None,
        description="Relevant text snippet from the output or check result",
    )
    locator: str | None = Field(
        default=None,
        description="Location reference (line number, tool call index, span range, etc.)",
    )


class ProbeResult(BaseSchema):
    """Result of executing a single probe."""

    version: str = Field(default="1.0.0", description="Schema version")
    result_id: str = Field(..., description="Unique result identifier")
    probe_id: str = Field(..., description="Reference to executed probe")
    verdict: ProbeVerdict = Field(..., description="Pass/Fail/Uncertain/Error")
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in verdict (0-1, optional)",
    )
    evidence: list[Evidence] = Field(
        default_factory=list, description="Supporting evidence"
    )
    failure_labels: list[FailureLabel] = Field(
        default_factory=list, description="Taxonomy labels if failed"
    )
    reasoning: str = Field(..., description="Explanation of the verdict")
    executed_at: datetime = Field(
        ..., description="When the probe was executed"
    )
