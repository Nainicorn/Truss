"""Decision schema for evaluation outcomes."""

from datetime import datetime

from pydantic import Field, model_validator

from schemas.base import BaseSchema, DecisionVerdict, utc_now


class Decision(BaseSchema):
    """Final decision on a candidate output."""

    version: str = Field(default="1.0.0", description="Schema version")
    decision_id: str = Field(..., description="Unique decision identifier")
    task_id: str = Field(..., description="Reference to parent task")
    candidate_id: str = Field(..., description="Reference to candidate output")
    verdict: DecisionVerdict = Field(
        ..., description="ACCEPT/REVISE/CONSTRAIN/ESCALATE"
    )
    rationale: str = Field(..., description="Explanation for the decision")
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in decision (0-1, optional)",
    )
    failed_probe_ids: list[str] = Field(
        default_factory=list, description="Probe IDs that failed"
    )
    revision_guidance: str | None = Field(
        default=None,
        description="Guidance for revision (required if verdict=REVISE)",
    )
    created_at: datetime = Field(
        default_factory=utc_now, description="When decision was made"
    )

    @model_validator(mode="after")
    def validate_revise_guidance(self) -> "Decision":
        """Require revision_guidance if verdict is REVISE."""
        if (
            self.verdict == DecisionVerdict.REVISE
            and not self.revision_guidance
        ):
            raise ValueError(
                "revision_guidance required when verdict=REVISE"
            )
        return self
