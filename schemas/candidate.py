"""Candidate output schema."""

from datetime import datetime
from typing import Any

from pydantic import Field

from schemas.base import BaseSchema, utc_now


class ToolCall(BaseSchema):
    """Record of a single tool invocation."""

    tool_name: str = Field(..., description="Name of the tool called")
    arguments: dict[str, Any] = Field(
        ..., description="Arguments passed to the tool"
    )
    result: Any | None = Field(
        default=None, description="Result returned by the tool"
    )
    timestamp: datetime = Field(..., description="When the tool was called")


class CandidateOutput(BaseSchema):
    """Output from a candidate (model or agent).

    Includes the main content response and optional tool call trace.
    """

    version: str = Field(default="1.0.0", description="Schema version")
    candidate_id: str = Field(..., description="Unique candidate identifier")
    content: str = Field(..., description="Main response content")
    tool_calls: list[ToolCall] = Field(
        default_factory=list, description="Sequence of tool invocations"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when output was created",
    )
