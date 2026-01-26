"""LangGraph evaluation pipeline - 6 nodes, linear flow."""

import time
from datetime import datetime

from langgraph.graph import StateGraph, START, END

from graphs.state import GraphState
from probes import InstructionComplianceProbe, SchemaValidationProbe, ConsistencyCheckProbe
from schemas import (
    TaskSpec,
    CandidateOutput,
    DecisionVerdict,
    ProbeVerdict,
    generate_id,
    utc_now,
    NodeStatus,
    FailureLabel,
)
from schemas.probe import ProbePlan, ProbeDefinition, ProbeResult as ProbeResultSchema
from schemas.decision import Decision
from schemas.trace import AuditTrace, NodeEvent
from schemas.run import RunRecord


def normalize_input(state: GraphState) -> GraphState:
    """Initialize run metadata and start timing.

    Sets: run_id, started_at, node_events (with STARTED), config_snapshot
    """
    run_id = generate_id("run")
    started_at = utc_now()

    node_event = NodeEvent(
        node_name="normalize_input",
        started_at=started_at,
        completed_at=started_at,
        duration_ms=0,
        status=NodeStatus.STARTED,
    )

    config_snapshot = {
        "phase": "2",
        "probe_count": 3,
        "schema_versions": {
            "task_spec": "1.0.0",
            "candidate_output": "1.0.0",
            "probe_plan": "1.0.0",
            "probe_result": "1.0.0",
            "decision": "1.0.0",
            "audit_trace": "1.0.0",
            "run_record": "1.0.0",
        },
        "model_spec": {
            "name": "placeholder",
            "version": "0.1.0",
        },
    }

    return {
        **state,
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "node_events": [node_event],  # Keep as NodeEvent instance, not dict
        "tool_events": [],
        "config_snapshot": config_snapshot,
    }


def generate_probe_plan(state: GraphState) -> GraphState:
    """Create ProbePlan with exactly 3 probes."""
    task_id = state["task_spec"]["task_id"]
    candidate_id = state["candidate_output"]["candidate_id"]
    started = utc_now()

    # Create exactly 3 probes (hardcoded)
    probes = [
        ProbeDefinition(
            probe_id=generate_id("probe"),
            probe_type="instruction_compliance",
            description="Check if constraints are addressed",
            rationale="Verify candidate output addresses all task constraints",
        ),
        ProbeDefinition(
            probe_id=generate_id("probe"),
            probe_type="schema_validation",
            description="Validate output schema compliance",
            rationale="Ensure output structure is valid and complete",
        ),
        ProbeDefinition(
            probe_id=generate_id("probe"),
            probe_type="consistency_check",
            description="Check for internal contradictions",
            rationale="Detect logical inconsistencies and format issues",
        ),
    ]

    plan = ProbePlan(
        plan_id=generate_id("plan"),
        task_id=task_id,
        candidate_id=candidate_id,
        probes=probes,
    )

    completed = utc_now()
    node_event = NodeEvent(
        node_name="generate_probe_plan",
        started_at=started,
        completed_at=completed,
        duration_ms=int((completed - started).total_seconds() * 1000),
        status=NodeStatus.COMPLETED,
    )

    return {
        **state,
        "probe_plan": plan.model_dump(),
        "node_events": state["node_events"] + [node_event],
    }


def execute_probes(state: GraphState) -> GraphState:
    """Execute all 3 probes and collect results with evidence."""
    started = utc_now()
    task = TaskSpec.model_validate(state["task_spec"])
    candidate = CandidateOutput.model_validate(state["candidate_output"])

    # Probe instances
    probes = [
        InstructionComplianceProbe(),
        SchemaValidationProbe(),
        ConsistencyCheckProbe(),
    ]

    results = []
    for probe in probes:
        result = probe.run(task, candidate)
        results.append(result.model_dump())

    completed = utc_now()
    node_event = NodeEvent(
        node_name="execute_probes",
        started_at=started,
        completed_at=completed,
        duration_ms=int((completed - started).total_seconds() * 1000),
        status=NodeStatus.COMPLETED,
    )

    return {
        **state,
        "probe_results": results,
        "node_events": state["node_events"] + [node_event],
    }


def classify_failures(state: GraphState) -> GraphState:
    """Classify failures by adding FailureLabel to FAIL/ERROR verdicts."""
    started = utc_now()

    updated_results = []
    for result_dict in state["probe_results"]:
        # Reconstruct ProbeResult instance
        result = ProbeResultSchema.model_validate(result_dict)
        verdict_str = result_dict.get("verdict")

        # Add labels for failed verdicts
        if verdict_str in [ProbeVerdict.FAIL.value, ProbeVerdict.ERROR.value]:
            probe_type = None
            # Infer from probe_id if possible
            for probe_def in state["probe_plan"]["probes"]:
                if probe_def["probe_id"] == result.probe_id:
                    probe_type = probe_def["probe_type"]
                    break

            labels = []
            if probe_type == "instruction_compliance":
                labels.append(FailureLabel.INSTRUCTION_VIOLATION)
            elif probe_type == "schema_validation":
                labels.append(FailureLabel.SCHEMA_VIOLATION)
            elif probe_type == "consistency_check":
                labels.append(FailureLabel.INCONSISTENCY)
            else:
                labels.append(FailureLabel.OTHER)

            # Update the result with new labels
            result.failure_labels = labels

        # Dump back to dict for state storage
        updated_results.append(result.model_dump())

    completed = utc_now()
    node_event = NodeEvent(
        node_name="classify_failures",
        started_at=started,
        completed_at=completed,
        duration_ms=int((completed - started).total_seconds() * 1000),
        status=NodeStatus.COMPLETED,
    )

    return {
        **state,
        "probe_results": updated_results,
        "node_events": state["node_events"] + [node_event],
    }


def decide_outcome(state: GraphState) -> GraphState:
    """Determine final decision based on probe verdicts.

    Decision mapping:
    - All PASS → ACCEPT
    - Any FAIL → REVISE
    - Any UNCERTAIN → CONSTRAIN
    - Any ERROR → ESCALATE
    """
    started = utc_now()

    # Count verdict types
    verdicts = [r.get("verdict") for r in state["probe_results"]]
    error_count = sum(1 for v in verdicts if v == ProbeVerdict.ERROR.value)
    fail_count = sum(1 for v in verdicts if v == ProbeVerdict.FAIL.value)
    uncertain_count = sum(
        1 for v in verdicts if v == ProbeVerdict.UNCERTAIN.value
    )
    pass_count = sum(1 for v in verdicts if v == ProbeVerdict.PASS.value)

    # Decision logic (priority: ERROR > FAIL > UNCERTAIN > PASS)
    if error_count > 0:
        verdict = DecisionVerdict.ESCALATE
        rationale = f"Encountered {error_count} probe error(s)"
        guidance = None
    elif fail_count > 0:
        verdict = DecisionVerdict.REVISE
        rationale = f"{fail_count} probe(s) failed"
        guidance = "Address findings from failed probes and resubmit"
    elif uncertain_count > 0:
        verdict = DecisionVerdict.CONSTRAIN
        rationale = f"{uncertain_count} probe(s) uncertain"
        guidance = None
    else:
        verdict = DecisionVerdict.ACCEPT
        rationale = f"All {pass_count} probe(s) passed"
        guidance = None

    # Get failed probe IDs
    failed_probe_ids = [
        r["probe_id"]
        for r in state["probe_results"]
        if r.get("verdict") in [
            ProbeVerdict.FAIL.value,
            ProbeVerdict.ERROR.value,
            ProbeVerdict.UNCERTAIN.value,
        ]
    ]

    decision = Decision(
        decision_id=generate_id("decision"),
        task_id=state["task_spec"]["task_id"],
        candidate_id=state["candidate_output"]["candidate_id"],
        verdict=verdict,
        rationale=rationale,
        failed_probe_ids=failed_probe_ids,
        revision_guidance=guidance,
    )

    completed = utc_now()
    node_event = NodeEvent(
        node_name="decide_outcome",
        started_at=started,
        completed_at=completed,
        duration_ms=int((completed - started).total_seconds() * 1000),
        status=NodeStatus.COMPLETED,
    )

    return {
        **state,
        "decision": decision.model_dump(),
        "node_events": state["node_events"] + [node_event],
    }


def finalize_trace(state: GraphState) -> GraphState:
    """Assemble complete AuditTrace and RunRecord."""
    started = utc_now()
    started_dt = datetime.fromisoformat(state["started_at"])
    completed = utc_now()

    # Calculate total duration
    total_duration_ms = int((completed - started_dt).total_seconds() * 1000)

    # Create AuditTrace with node_events (already NodeEvent instances)
    trace = AuditTrace(
        trace_id=generate_id("trace"),
        run_id=state["run_id"],
        task_id=state["task_spec"]["task_id"],
        candidate_id=state["candidate_output"]["candidate_id"],
        started_at=started_dt,
        completed_at=completed,
        total_duration_ms=total_duration_ms,
        node_events=state["node_events"],
        tool_events=state["tool_events"],
        config_snapshot=state["config_snapshot"],
    )

    # Assemble RunRecord
    run_record = RunRecord(
        run_id=state["run_id"],
        task_spec=state["task_spec"],
        candidate_output=state["candidate_output"],
        probe_plan=state["probe_plan"],
        probe_results=state["probe_results"],
        decision=state["decision"],
        audit_trace=trace.model_dump(),
        config_snapshot=state["config_snapshot"],
    )

    # Record final event
    node_event = NodeEvent(
        node_name="finalize_trace",
        started_at=started,
        completed_at=completed,
        duration_ms=int((completed - started).total_seconds() * 1000),
        status=NodeStatus.COMPLETED,
    )

    return {
        **state,
        "audit_trace": trace.model_dump(),
        "run_record": run_record.model_dump(),
        "node_events": state["node_events"] + [node_event],
    }


def create_graph():
    """Build and compile the evaluation graph."""
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("normalize_input", normalize_input)
    graph.add_node("generate_probe_plan", generate_probe_plan)
    graph.add_node("execute_probes", execute_probes)
    graph.add_node("classify_failures", classify_failures)
    graph.add_node("decide_outcome", decide_outcome)
    graph.add_node("finalize_trace", finalize_trace)

    # Add edges (linear flow)
    graph.add_edge(START, "normalize_input")
    graph.add_edge("normalize_input", "generate_probe_plan")
    graph.add_edge("generate_probe_plan", "execute_probes")
    graph.add_edge("execute_probes", "classify_failures")
    graph.add_edge("classify_failures", "decide_outcome")
    graph.add_edge("decide_outcome", "finalize_trace")
    graph.add_edge("finalize_trace", END)

    # Compile
    return graph.compile()
