"""Tests for Polaris schemas - round-trip, validation, and JSON schema."""

import pytest
from pydantic import ValidationError

from schemas import (
    AuditTrace,
    CandidateOutput,
    Decision,
    DecisionVerdict,
    EvidenceSource,
    FailureLabel,
    NodeEvent,
    NodeStatus,
    ProbePlan,
    ProbeDefinition,
    ProbeResult,
    ProbeVerdict,
    TaskSpec,
    ToolCall,
    Evidence,
    generate_id,
    utc_now,
)
from schemas.run import RunRecord


class TestTaskSpec:
    """Tests for TaskSpec schema."""

    def test_taskspec_minimal(self):
        """Test minimal valid TaskSpec."""
        spec = TaskSpec(
            task_id="task_001",
            description="Evaluate summarization quality",
        )
        assert spec.task_id == "task_001"
        assert spec.version == "1.0.0"
        assert spec.allowed_tools is None
        assert len(spec.constraints) == 0

    def test_taskspec_full(self):
        """Test TaskSpec with all fields."""
        spec = TaskSpec(
            task_id="task_002",
            description="Complex task",
            constraints=["Must cite sources", "Max 200 words"],
            allowed_tools=["search", "calculator"],
            domain_tags=["research", "medical"],
            rubric_id="rubric_123",
        )
        assert spec.rubric_id == "rubric_123"
        assert len(spec.constraints) == 2
        assert len(spec.domain_tags) == 2

    def test_taskspec_roundtrip(self):
        """Test JSON serialization round-trip via semantic equality."""
        spec = TaskSpec(
            task_id="task_003",
            description="Test task",
            constraints=["Must cite sources"],
            allowed_tools=["search"],
            domain_tags=["research"],
        )

        # Serialize to JSON
        json_str = spec.model_dump_json()

        # Deserialize back
        restored = TaskSpec.model_validate_json(json_str)

        # Should be semantically identical
        assert restored == spec
        assert restored.constraints == spec.constraints
        assert restored.allowed_tools == spec.allowed_tools

    def test_taskspec_json_schema(self):
        """Test JSON schema export contains required keys."""
        schema = TaskSpec.model_json_schema()
        assert "properties" in schema
        assert "required" in schema
        assert "task_id" in schema["required"]
        assert "description" in schema["required"]
        assert "version" in schema["properties"]

    def test_taskspec_rejects_extra_fields(self):
        """Test that unknown fields are rejected (extra='forbid')."""
        with pytest.raises(ValidationError) as exc_info:
            TaskSpec(
                task_id="task_004",
                description="Test",
                unknown_field="should fail",
            )

        assert "extra" in str(exc_info.value).lower() and "not permitted" in str(exc_info.value).lower()

    def test_taskspec_requires_description(self):
        """Test that description is required and non-empty."""
        with pytest.raises(ValidationError):
            TaskSpec(task_id="task_005", description="")


class TestCandidateOutput:
    """Tests for CandidateOutput schema."""

    def test_candidate_output_minimal(self):
        """Test minimal CandidateOutput."""
        output = CandidateOutput(
            candidate_id="cand_001",
            content="Here is my response",
        )
        assert output.candidate_id == "cand_001"
        assert output.content == "Here is my response"
        assert len(output.tool_calls) == 0

    def test_candidate_output_with_tool_calls(self):
        """Test CandidateOutput with tool invocations."""
        now = utc_now()
        tool_call = ToolCall(
            tool_name="search",
            arguments={"query": "example"},
            result="Found: example.com",
            timestamp=now,
        )
        output = CandidateOutput(
            candidate_id="cand_002",
            content="Based on search results...",
            tool_calls=[tool_call],
            metadata={"model": "gpt-4"},
        )
        assert len(output.tool_calls) == 1
        assert output.tool_calls[0].tool_name == "search"
        assert output.metadata["model"] == "gpt-4"

    def test_candidate_output_roundtrip(self):
        """Test CandidateOutput round-trip."""
        now = utc_now()
        output = CandidateOutput(
            candidate_id="cand_003",
            content="Test response",
            tool_calls=[
                ToolCall(
                    tool_name="calc",
                    arguments={"expr": "2+2"},
                    result=4,
                    timestamp=now,
                )
            ],
            metadata={"version": "1"},
        )

        json_str = output.model_dump_json()
        restored = CandidateOutput.model_validate_json(json_str)

        assert restored == output
        assert len(restored.tool_calls) == 1


class TestProbeSchemas:
    """Tests for probe-related schemas."""

    def test_probe_plan_minimal(self):
        """Test minimal ProbePlan."""
        probe = ProbeDefinition(
            probe_id="probe_001",
            probe_type="instruction_compliance",
            description="Check instruction compliance",
            rationale="Ensure output follows instructions",
        )
        plan = ProbePlan(
            plan_id="plan_001",
            task_id="task_001",
            candidate_id="cand_001",
            probes=[probe],
        )
        assert len(plan.probes) == 1
        assert plan.probes[0].probe_type == "instruction_compliance"

    def test_probe_plan_max_probes_enforced(self):
        """Test that ProbePlan enforces max 8 probes."""
        probes = [
            ProbeDefinition(
                probe_id=f"probe_{i:03d}",
                probe_type="test",
                description=f"Probe {i}",
                rationale=f"Reason {i}",
            )
            for i in range(9)
        ]
        with pytest.raises(ValidationError) as exc_info:
            ProbePlan(
                plan_id="plan_002",
                task_id="task_002",
                candidate_id="cand_002",
                probes=probes,
            )

        assert "Maximum 8 probes" in str(exc_info.value)

    def test_probe_plan_min_probes_enforced(self):
        """Test that ProbePlan requires at least 1 probe."""
        with pytest.raises(ValidationError) as exc_info:
            ProbePlan(
                plan_id="plan_003",
                task_id="task_003",
                candidate_id="cand_003",
                probes=[],
            )

        assert "At least 1 probe" in str(exc_info.value)

    def test_evidence_source_enum(self):
        """Test Evidence.source must be EvidenceSource enum."""
        evidence = Evidence(
            source=EvidenceSource.TEXT_SPAN,
            excerpt="Example text",
            locator="line:42",
        )
        assert evidence.source == EvidenceSource.TEXT_SPAN
        assert evidence.locator == "line:42"

    def test_evidence_rejects_invalid_source(self):
        """Test that invalid source strings are rejected."""
        with pytest.raises(ValidationError):
            Evidence(
                source="INVALID_SOURCE",  # type: ignore
                excerpt="text",
            )

    def test_probe_result_optional_confidence(self):
        """Test ProbeResult can omit confidence."""
        result = ProbeResult(
            result_id="res_001",
            probe_id="probe_001",
            verdict=ProbeVerdict.UNCERTAIN,
            confidence=None,
            evidence=[],
            reasoning="Insufficient data",
            executed_at=utc_now(),
        )
        assert result.confidence is None
        assert result.verdict == ProbeVerdict.UNCERTAIN

    def test_probe_result_confidence_bounded(self):
        """Test ProbeResult confidence is bounded 0-1."""
        with pytest.raises(ValidationError):
            ProbeResult(
                result_id="res_002",
                probe_id="probe_002",
                verdict=ProbeVerdict.PASS,
                confidence=1.5,  # Out of bounds
                evidence=[],
                reasoning="Test",
                executed_at=utc_now(),
            )

    def test_probe_result_roundtrip(self):
        """Test ProbeResult round-trip."""
        result = ProbeResult(
            result_id="res_003",
            probe_id="probe_003",
            verdict=ProbeVerdict.PASS,
            confidence=0.95,
            evidence=[
                Evidence(
                    source=EvidenceSource.SCHEMA_VALIDATION,
                    excerpt="Valid schema",
                    locator="field:name",
                )
            ],
            failure_labels=[],
            reasoning="All checks passed",
            executed_at=utc_now(),
        )

        json_str = result.model_dump_json()
        restored = ProbeResult.model_validate_json(json_str)

        assert restored == result
        assert len(restored.evidence) == 1


class TestDecision:
    """Tests for Decision schema."""

    def test_decision_accept(self):
        """Test ACCEPT decision."""
        decision = Decision(
            decision_id="dec_001",
            task_id="task_001",
            candidate_id="cand_001",
            verdict=DecisionVerdict.ACCEPT,
            rationale="All probes passed",
            confidence=0.99,
        )
        assert decision.verdict == DecisionVerdict.ACCEPT
        assert decision.confidence == 0.99

    def test_decision_revise_requires_guidance(self):
        """Test REVISE requires revision_guidance."""
        with pytest.raises(ValidationError) as exc_info:
            Decision(
                decision_id="dec_002",
                task_id="task_002",
                candidate_id="cand_002",
                verdict=DecisionVerdict.REVISE,
                rationale="Needs improvement",
            )

        assert "revision_guidance required" in str(exc_info.value)

    def test_decision_revise_with_guidance(self):
        """Test REVISE with guidance."""
        decision = Decision(
            decision_id="dec_003",
            task_id="task_003",
            candidate_id="cand_003",
            verdict=DecisionVerdict.REVISE,
            rationale="Needs improvement",
            revision_guidance="Please cite sources and expand summary",
            confidence=0.75,
        )
        assert decision.verdict == DecisionVerdict.REVISE
        assert decision.revision_guidance is not None

    def test_decision_optional_confidence(self):
        """Test Decision can omit confidence."""
        decision = Decision(
            decision_id="dec_004",
            task_id="task_004",
            candidate_id="cand_004",
            verdict=DecisionVerdict.CONSTRAIN,
            rationale="Limit to certain domains",
            confidence=None,
        )
        assert decision.confidence is None

    def test_decision_roundtrip(self):
        """Test Decision round-trip."""
        decision = Decision(
            decision_id="dec_005",
            task_id="task_005",
            candidate_id="cand_005",
            verdict=DecisionVerdict.ESCALATE,
            rationale="Safety concerns",
            failed_probe_ids=["probe_001", "probe_002"],
        )

        json_str = decision.model_dump_json()
        restored = Decision.model_validate_json(json_str)

        assert restored == decision


class TestAuditTrace:
    """Tests for AuditTrace schema."""

    def test_node_event_started(self):
        """Test NodeEvent with STARTED status."""
        event = NodeEvent(
            node_name="normalize_input",
            started_at=utc_now(),
            status=NodeStatus.STARTED,
        )
        assert event.status == NodeStatus.STARTED
        assert event.completed_at is None

    def test_node_event_completed(self):
        """Test NodeEvent with COMPLETED status."""
        now = utc_now()
        event = NodeEvent(
            node_name="execute_probes",
            started_at=now,
            completed_at=now,
            duration_ms=1500,
            status=NodeStatus.COMPLETED,
        )
        assert event.status == NodeStatus.COMPLETED
        assert event.duration_ms == 1500

    def test_node_event_failed(self):
        """Test NodeEvent with FAILED status."""
        event = NodeEvent(
            node_name="finalize_trace",
            started_at=utc_now(),
            status=NodeStatus.FAILED,
            error="Database connection timeout",
        )
        assert event.status == NodeStatus.FAILED
        assert "timeout" in event.error.lower()

    def test_audit_trace_minimal(self):
        """Test minimal AuditTrace."""
        trace = AuditTrace(
            trace_id="trace_001",
            run_id="run_001",
            task_id="task_001",
            candidate_id="cand_001",
            started_at=utc_now(),
        )
        assert len(trace.node_events) == 0
        assert len(trace.tool_events) == 0

    def test_audit_trace_with_events(self):
        """Test AuditTrace with node and tool events."""
        now = utc_now()
        trace = AuditTrace(
            trace_id="trace_002",
            run_id="run_002",
            task_id="task_002",
            candidate_id="cand_002",
            started_at=now,
            completed_at=now,
            total_duration_ms=5000,
            node_events=[
                NodeEvent(
                    node_name="normalize",
                    started_at=now,
                    status=NodeStatus.COMPLETED,
                    duration_ms=100,
                )
            ],
            config_snapshot={"model": "gpt-4", "rubric_version": "1.0"},
        )
        assert len(trace.node_events) == 1
        assert trace.config_snapshot["model"] == "gpt-4"

    def test_audit_trace_roundtrip(self):
        """Test AuditTrace round-trip."""
        now = utc_now()
        trace = AuditTrace(
            trace_id="trace_003",
            run_id="run_003",
            task_id="task_003",
            candidate_id="cand_003",
            started_at=now,
            node_events=[
                NodeEvent(
                    node_name="test_node",
                    started_at=now,
                    status=NodeStatus.COMPLETED,
                )
            ],
        )

        json_str = trace.model_dump_json()
        restored = AuditTrace.model_validate_json(json_str)

        assert restored == trace


class TestRunRecord:
    """Tests for RunRecord schema."""

    def test_runrecord_minimal(self):
        """Test minimal RunRecord with just task and output."""
        task = TaskSpec(task_id="task_001", description="Test task")
        output = CandidateOutput(
            candidate_id="cand_001", content="Response"
        )
        record = RunRecord(
            run_id="run_001", task_spec=task, candidate_output=output
        )
        assert record.task_spec.task_id == "task_001"
        assert record.probe_plan is None
        assert record.decision is None
        assert record.audit_trace is None

    def test_runrecord_intermediate_state(self):
        """Test RunRecord with probe plan but no decision yet."""
        task = TaskSpec(task_id="task_002", description="Test")
        output = CandidateOutput(candidate_id="cand_002", content="Response")
        probe = ProbeDefinition(
            probe_id="probe_001",
            probe_type="test",
            description="Test probe",
            rationale="Test",
        )
        plan = ProbePlan(
            plan_id="plan_001",
            task_id="task_002",
            candidate_id="cand_002",
            probes=[probe],
        )
        record = RunRecord(
            run_id="run_002",
            task_spec=task,
            candidate_output=output,
            probe_plan=plan,
        )
        assert record.probe_plan is not None
        assert record.decision is None

    def test_runrecord_complete_state(self):
        """Test RunRecord with all fields populated."""
        now = utc_now()
        task = TaskSpec(task_id="task_003", description="Complete test")
        output = CandidateOutput(candidate_id="cand_003", content="Response")
        probe = ProbeDefinition(
            probe_id="probe_001",
            probe_type="test",
            description="Test",
            rationale="Test",
        )
        plan = ProbePlan(
            plan_id="plan_001",
            task_id="task_003",
            candidate_id="cand_003",
            probes=[probe],
        )
        result = ProbeResult(
            result_id="res_001",
            probe_id="probe_001",
            verdict=ProbeVerdict.PASS,
            evidence=[],
            reasoning="Passed",
            executed_at=now,
        )
        decision = Decision(
            decision_id="dec_001",
            task_id="task_003",
            candidate_id="cand_003",
            verdict=DecisionVerdict.ACCEPT,
            rationale="All good",
        )
        trace = AuditTrace(
            trace_id="trace_001",
            run_id="run_003",
            task_id="task_003",
            candidate_id="cand_003",
            started_at=now,
        )
        record = RunRecord(
            run_id="run_003",
            task_spec=task,
            candidate_output=output,
            probe_plan=plan,
            probe_results=[result],
            decision=decision,
            audit_trace=trace,
            config_snapshot={"version": "1.0"},
        )
        assert record.probe_plan is not None
        assert record.decision is not None
        assert record.audit_trace is not None
        assert len(record.probe_results) == 1

    def test_runrecord_roundtrip(self):
        """Test RunRecord round-trip."""
        task = TaskSpec(task_id="task_004", description="Roundtrip test")
        output = CandidateOutput(
            candidate_id="cand_004",
            content="Test response",
            metadata={"source": "test"},
        )
        record = RunRecord(
            run_id="run_004",
            task_spec=task,
            candidate_output=output,
            config_snapshot={"model": "test-v1"},
        )

        json_str = record.model_dump_json()
        restored = RunRecord.model_validate_json(json_str)

        assert restored == record
        assert restored.config_snapshot["model"] == "test-v1"

    def test_runrecord_json_schema(self):
        """Test RunRecord JSON schema export."""
        schema = RunRecord.model_json_schema()
        assert "properties" in schema
        assert "required" in schema
        assert "run_id" in schema["required"]
        assert "task_spec" in schema["required"]
        assert "candidate_output" in schema["required"]


class TestEnums:
    """Tests for all enum types."""

    def test_decision_verdicts(self):
        """Test all DecisionVerdict values."""
        assert DecisionVerdict.ACCEPT.value == "ACCEPT"
        assert DecisionVerdict.REVISE.value == "REVISE"
        assert DecisionVerdict.CONSTRAIN.value == "CONSTRAIN"
        assert DecisionVerdict.ESCALATE.value == "ESCALATE"

    def test_probe_verdicts(self):
        """Test all ProbeVerdict values."""
        assert ProbeVerdict.PASS.value == "PASS"
        assert ProbeVerdict.FAIL.value == "FAIL"
        assert ProbeVerdict.UNCERTAIN.value == "UNCERTAIN"
        assert ProbeVerdict.ERROR.value == "ERROR"

    def test_node_statuses(self):
        """Test all NodeStatus values."""
        assert NodeStatus.STARTED.value == "STARTED"
        assert NodeStatus.COMPLETED.value == "COMPLETED"
        assert NodeStatus.FAILED.value == "FAILED"

    def test_failure_labels(self):
        """Test all FailureLabel values."""
        assert FailureLabel.INSTRUCTION_VIOLATION.value == "INSTRUCTION_VIOLATION"
        assert FailureLabel.HALLUCINATION.value == "HALLUCINATION"
        assert FailureLabel.SAFETY_CONCERN.value == "SAFETY_CONCERN"

    def test_evidence_sources(self):
        """Test all EvidenceSource values."""
        assert EvidenceSource.TEXT_SPAN.value == "TEXT_SPAN"
        assert EvidenceSource.TOOL_OUTPUT.value == "TOOL_OUTPUT"
        assert EvidenceSource.SCHEMA_VALIDATION.value == "SCHEMA_VALIDATION"
        assert EvidenceSource.CONSISTENCY_CHECK.value == "CONSISTENCY_CHECK"
        assert EvidenceSource.OTHER.value == "OTHER"


class TestUtilities:
    """Tests for utility functions."""

    def test_utc_now_timezone_aware(self):
        """Test utc_now returns timezone-aware datetime."""
        now = utc_now()
        assert now.tzinfo is not None

    def test_generate_id(self):
        """Test generate_id creates properly formatted IDs."""
        id1 = generate_id("task")
        id2 = generate_id("task")
        assert id1.startswith("task_")
        assert id2.startswith("task_")
        assert id1 != id2  # Should be unique
        assert len(id1) == 17  # "task_" + 12 hex chars

    def test_generate_id_different_prefixes(self):
        """Test generate_id with different prefixes."""
        probe_id = generate_id("probe")
        trace_id = generate_id("trace")
        assert probe_id.startswith("probe_")
        assert trace_id.startswith("trace_")


class TestSemanticDeterminism:
    """Tests for semantic determinism (not field-order)."""

    def test_taskspec_semantic_equality(self):
        """Test TaskSpec objects are equal semantically after round-trip."""
        spec1 = TaskSpec(
            task_id="t1",
            description="desc",
            constraints=["c1"],
            allowed_tools=["tool1"],
        )
        json_str = spec1.model_dump_json()
        spec2 = TaskSpec.model_validate_json(json_str)

        # Semantic equality
        assert spec1 == spec2
        # Not comparing JSON strings (no field-order assertion)

    def test_complex_schema_semantic_equality(self):
        """Test complex nested schema semantic equality."""
        now = utc_now()
        result1 = ProbeResult(
            result_id="r1",
            probe_id="p1",
            verdict=ProbeVerdict.PASS,
            confidence=0.9,
            evidence=[
                Evidence(
                    source=EvidenceSource.TEXT_SPAN,
                    excerpt="text",
                    locator="loc",
                ),
                Evidence(
                    source=EvidenceSource.TOOL_OUTPUT,
                    excerpt="output",
                ),
            ],
            failure_labels=[FailureLabel.HALLUCINATION],
            reasoning="test",
            executed_at=now,
        )
        json_str = result1.model_dump_json()
        result2 = ProbeResult.model_validate_json(json_str)

        # Should be equal
        assert result1 == result2
        assert len(result1.evidence) == len(result2.evidence)
