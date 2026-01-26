"""LangGraph state definition for evaluation pipeline."""

from typing import Any, TypedDict


class GraphState(TypedDict):
    """Evaluation graph state - must be JSON-serializable.

    Flows through 6 nodes:
    normalize_input → generate_probe_plan → execute_probes →
    classify_failures → decide_outcome → finalize_trace
    """

    # Input (provided by user)
    task_spec: dict[str, Any]  # TaskSpec.model_dump()
    candidate_output: dict[str, Any]  # CandidateOutput.model_dump()

    # Generated during run
    run_id: str
    started_at: str  # ISO8601 timestamp
    probe_plan: dict[str, Any] | None  # ProbePlan.model_dump()
    probe_results: list[dict[str, Any]]  # [ProbeResult.model_dump()]
    decision: dict[str, Any] | None  # Decision.model_dump()
    audit_trace: dict[str, Any] | None  # AuditTrace.model_dump()
    run_record: dict[str, Any] | None  # RunRecord.model_dump()

    # Metadata for audit trail
    node_events: list[dict[str, Any]]  # [NodeEvent.model_dump()]
    tool_events: list[dict[str, Any]]  # [ToolEvent.model_dump()]
    config_snapshot: dict[str, Any]  # {phase, probe_count, schema_versions, model_spec}
