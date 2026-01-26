"""Audit trace schema for tracking evaluation execution."""

from datetime import datetime
from typing import Any

from pydantic import Field

from schemas.base import BaseSchema, NodeStatus, utc_now


class NodeEvent(BaseSchema):
    """Event in the evaluation pipeline (node execution)."""

    node_name: str = Field(..., description="Name of the node")
    started_at: datetime = Field(..., description="When the node started")
    completed_at: datetime | None = Field(
        default=None, description="When the node completed"
    )
    duration_ms: int | None = Field(
        default=None, description="Execution duration in milliseconds"
    )
    status: NodeStatus = Field(..., description="STARTED/COMPLETED/FAILED")
    error: str | None = Field(
        default=None, description="Error message if status=FAILED"
    )


class ToolEvent(BaseSchema):
    """Tool invocation event during evaluation."""

    tool_name: str = Field(..., description="Name of the tool")
    arguments: dict[str, Any] = Field(..., description="Tool arguments")
    result: Any | None = Field(
        default=None, description="Tool result (if completed)"
    )
    timestamp: datetime = Field(..., description="When tool was invoked")
    duration_ms: int | None = Field(
        default=None, description="Execution duration in milliseconds"
    )


class AuditTrace(BaseSchema):
    """Complete audit trail of an evaluation run."""

    version: str = Field(default="1.0.0", description="Schema version")
    trace_id: str = Field(..., description="Unique trace identifier")
    run_id: str = Field(..., description="Reference to parent run")
    task_id: str = Field(..., description="Reference to task")
    candidate_id: str = Field(..., description="Reference to candidate")
    started_at: datetime = Field(..., description="When run started")
    completed_at: datetime | None = Field(
        default=None, description="When run completed"
    )
    total_duration_ms: int | None = Field(
        default=None, description="Total execution time in milliseconds"
    )
    node_events: list[NodeEvent] = Field(
        default_factory=list, description="Timeline of node executions"
    )
    tool_events: list[ToolEvent] = Field(
        default_factory=list, description="Timeline of tool invocations"
    )
    artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description="References to ProbePlan, Decision, etc.",
    )
    config_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Model version, rubric version, probe suite version",
    )
