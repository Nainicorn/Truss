"""Complete evaluation run schema."""

from datetime import datetime
from typing import Any

from pydantic import Field

from schemas.base import BaseSchema, utc_now
from schemas.candidate import CandidateOutput
from schemas.decision import Decision
from schemas.probe import ProbePlan, ProbeResult
from schemas.task import TaskSpec
from schemas.trace import AuditTrace


class RunRecord(BaseSchema):
    """Complete evaluation run tying all schemas together.

    A RunRecord represents one evaluation run from start to finish,
    containing the task, candidate output, probe plan, results, decision,
    and audit trace. Intermediate states are allowed (e.g., run may have
    ProbePlan but not yet Decision).
    """

    version: str = Field(default="1.0.0", description="Schema version")
    run_id: str = Field(..., description="Unique run identifier")
    task_spec: TaskSpec = Field(..., description="Task specification")
    candidate_output: CandidateOutput = Field(..., description="Candidate output")
    probe_plan: ProbePlan | None = Field(
        default=None,
        description="Probe plan (None if run hasn't reached planning stage)",
    )
    probe_results: list[ProbeResult] = Field(
        default_factory=list, description="Results from executed probes"
    )
    decision: Decision | None = Field(
        default=None,
        description="Final decision (None if run hasn't reached decision stage)",
    )
    audit_trace: AuditTrace | None = Field(
        default=None,
        description="Complete audit trail (None if trace not finalized)",
    )
    config_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Model version, rubric version, probe suite version, etc.",
    )
    created_at: datetime = Field(
        default_factory=utc_now, description="When run was created"
    )
