"""Integration tests for evaluation graph."""

import pytest

from graphs import create_graph
from schemas import TaskSpec, CandidateOutput, DecisionVerdict, utc_now
from schemas.run import RunRecord


class TestEvalGraphIntegration:
    """Integration tests for the evaluation pipeline."""

    def test_eval_graph_end_to_end(self):
        """Test graph produces valid RunRecord with all required fields."""
        # Create test inputs
        task = TaskSpec(
            task_id="test_task_001",
            description="Test task",
            constraints=["Must mention constraint"],
        )
        candidate = CandidateOutput(
            candidate_id="test_cand_001",
            content="This response mentions constraint clearly",
        )

        # Run graph
        graph = create_graph()
        result = graph.invoke({
            "task_spec": task.model_dump(),
            "candidate_output": candidate.model_dump(),
        })

        # Validate RunRecord
        record = RunRecord.model_validate(result["run_record"])

        # Basic assertions
        assert record.run_id is not None
        assert record.run_id.startswith("run_")
        assert record.task_spec is not None
        assert record.candidate_output is not None

    def test_eval_graph_produces_complete_runrecord(self):
        """Test graph populates all RunRecord fields."""
        task = TaskSpec(
            task_id="test_task_002",
            description="Summarize something",
            constraints=["Must be short"],
        )
        candidate = CandidateOutput(
            candidate_id="test_cand_002",
            content="Must be short",
        )

        graph = create_graph()
        result = graph.invoke({
            "task_spec": task.model_dump(),
            "candidate_output": candidate.model_dump(),
        })

        record = RunRecord.model_validate(result["run_record"])

        # All fields must be present and populated
        assert record.run_id is not None
        assert record.task_spec is not None
        assert record.candidate_output is not None
        assert record.probe_plan is not None
        assert record.probe_results is not None
        assert len(record.probe_results) > 0
        assert record.decision is not None
        assert record.audit_trace is not None
        assert record.config_snapshot is not None

    def test_eval_graph_exactly_three_probes(self):
        """Test that exactly 3 probes are executed."""
        task = TaskSpec(
            task_id="test_task_003",
            description="Test",
            constraints=["constraint_1"],
        )
        candidate = CandidateOutput(
            candidate_id="test_cand_003",
            content="constraint_1 is mentioned",
        )

        graph = create_graph()
        result = graph.invoke({
            "task_spec": task.model_dump(),
            "candidate_output": candidate.model_dump(),
        })

        record = RunRecord.model_validate(result["run_record"])

        # Must have exactly 3 probes
        assert len(record.probe_plan.probes) == 3
        assert len(record.probe_results) == 3

    def test_eval_graph_probe_types(self):
        """Test that probe types match expected values."""
        task = TaskSpec(
            task_id="test_task_004",
            description="Test",
            constraints=[],
        )
        candidate = CandidateOutput(
            candidate_id="test_cand_004",
            content="Test content",
        )

        graph = create_graph()
        result = graph.invoke({
            "task_spec": task.model_dump(),
            "candidate_output": candidate.model_dump(),
        })

        record = RunRecord.model_validate(result["run_record"])

        # Check probe types (don't assert exact IDs)
        probe_types = {p.probe_type for p in record.probe_plan.probes}
        expected_types = {
            "instruction_compliance",
            "schema_validation",
            "consistency_check",
        }
        assert probe_types == expected_types

    def test_eval_graph_decision_verdicts(self):
        """Test that decision verdict is valid."""
        task = TaskSpec(
            task_id="test_task_005",
            description="Test",
            constraints=["must_be_present"],
        )
        candidate = CandidateOutput(
            candidate_id="test_cand_005",
            content="Test content without required mention",
        )

        graph = create_graph()
        result = graph.invoke({
            "task_spec": task.model_dump(),
            "candidate_output": candidate.model_dump(),
        })

        record = RunRecord.model_validate(result["run_record"])

        # Decision verdict must be one of the valid values
        assert record.decision.verdict in [
            DecisionVerdict.ACCEPT,
            DecisionVerdict.REVISE,
            DecisionVerdict.CONSTRAIN,
            DecisionVerdict.ESCALATE,
        ]

    def test_eval_graph_audit_trace_nodeevents(self):
        """Test AuditTrace contains NodeEvents with timing info."""
        task = TaskSpec(
            task_id="test_task_006",
            description="Test",
            constraints=[],
        )
        candidate = CandidateOutput(
            candidate_id="test_cand_006",
            content="Content",
        )

        graph = create_graph()
        result = graph.invoke({
            "task_spec": task.model_dump(),
            "candidate_output": candidate.model_dump(),
        })

        record = RunRecord.model_validate(result["run_record"])
        trace = record.audit_trace

        # Must have node events
        assert len(trace.node_events) > 0

        # Check each node event has required fields
        for event in trace.node_events:
            assert event.node_name is not None
            assert event.started_at is not None
            assert event.status is not None
            # completed_at and duration_ms may be None for in-progress nodes
            # but we expect COMPLETED nodes to have these

            if event.status.value == "COMPLETED":
                assert event.completed_at is not None
                assert event.duration_ms is not None
                assert event.duration_ms >= 0

        # Should have at least STARTED and COMPLETED events
        statuses = {e.status.value for e in trace.node_events}
        assert "COMPLETED" in statuses

    def test_eval_graph_config_snapshot(self):
        """Test config_snapshot contains required fields."""
        task = TaskSpec(
            task_id="test_task_007",
            description="Test",
            constraints=[],
        )
        candidate = CandidateOutput(
            candidate_id="test_cand_007",
            content="Content",
        )

        graph = create_graph()
        result = graph.invoke({
            "task_spec": task.model_dump(),
            "candidate_output": candidate.model_dump(),
        })

        record = RunRecord.model_validate(result["run_record"])

        # Check config_snapshot structure
        assert record.config_snapshot["phase"] == "2"
        assert record.config_snapshot["probe_count"] == 3
        assert "schema_versions" in record.config_snapshot
        assert "model_spec" in record.config_snapshot

        # Check schema versions
        schema_vers = record.config_snapshot["schema_versions"]
        assert schema_vers["task_spec"] == "1.0.0"
        assert schema_vers["candidate_output"] == "1.0.0"
        assert schema_vers["probe_plan"] == "1.0.0"
        assert schema_vers["probe_result"] == "1.0.0"
        assert schema_vers["decision"] == "1.0.0"
        assert schema_vers["audit_trace"] == "1.0.0"
        assert schema_vers["run_record"] == "1.0.0"

        # Check model spec
        model_spec = record.config_snapshot["model_spec"]
        assert model_spec["name"] == "placeholder"
        assert model_spec["version"] == "0.1.0"

    def test_eval_graph_evidence_policy(self):
        """Test evidence policy: FAIL/ERROR have evidence, PASS may be empty."""
        task = TaskSpec(
            task_id="test_task_008",
            description="Test",
            constraints=["mention_this"],
        )
        # Content that will fail instruction compliance (missing constraint)
        candidate = CandidateOutput(
            candidate_id="test_cand_008",
            content="This response does not contain the required constraint",
        )

        graph = create_graph()
        result = graph.invoke({
            "task_spec": task.model_dump(),
            "candidate_output": candidate.model_dump(),
        })

        record = RunRecord.model_validate(result["run_record"])

        # Check evidence policy for each result
        for result in record.probe_results:
            verdict = result.verdict.value if hasattr(result.verdict, 'value') else result.verdict
            evidence = result.evidence

            # FAIL/ERROR must have evidence
            if verdict in ["FAIL", "ERROR"]:
                assert len(evidence) > 0, (
                    f"Probe {result.probe_id} has {verdict} "
                    "but no evidence"
                )
            # PASS may have empty evidence
            elif verdict == "PASS":
                # No requirement, evidence is optional
                pass

    def test_eval_graph_all_pass_becomes_accept(self):
        """Test that all PASS verdicts lead to ACCEPT decision."""
        task = TaskSpec(
            task_id="test_task_009",
            description="Test",
            constraints=["include_this"],
        )
        # Content that addresses constraint and is consistent
        candidate = CandidateOutput(
            candidate_id="test_cand_009",
            content="This response includes_this constraint as required",
        )

        graph = create_graph()
        result = graph.invoke({
            "task_spec": task.model_dump(),
            "candidate_output": candidate.model_dump(),
        })

        record = RunRecord.model_validate(result["run_record"])

        # Check if all probes passed
        all_passed = all(
            (r.verdict.value if hasattr(r.verdict, 'value') else r.verdict) == "PASS"
            for r in record.probe_results
        )

        # If all passed, decision should be ACCEPT
        if all_passed:
            assert record.decision.verdict == DecisionVerdict.ACCEPT
