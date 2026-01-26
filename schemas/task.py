"""Task specification schema."""

from datetime import datetime
from typing import Any

from pydantic import Field

from schemas.base import BaseSchema, utc_now


class TaskSpec(BaseSchema):
    """Specification for an evaluation task.

    Defines what needs to be evaluated, constraints, allowed tools,
    and domain context.
    """

    version: str = Field(default="1.0.0", description="Schema version")
    task_id: str = Field(..., description="Unique task identifier")
    description: str = Field(..., min_length=1, description="Task description")
    constraints: list[str] = Field(
        default_factory=list,
        description="Constraints the candidate output must satisfy",
    )
    allowed_tools: list[str] | None = Field(
        default=None,
        description="Allowed tool names. None means all tools allowed.",
    )
    domain_tags: list[str] = Field(
        default_factory=list,
        description="Domain tags for categorization (e.g., 'medical', 'finance')",
    )
    rubric_id: str | None = Field(
        default=None,
        description="Reference to evaluation rubric. None means generate rubric.",
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when task was created",
    )
