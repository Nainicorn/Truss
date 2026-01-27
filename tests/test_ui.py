"""Tests for UI pages and report generation."""

import json
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from psycopg import AsyncConnection

from server.main import app
from server.report_generator import generate_report_md
from schemas import TaskSpec, CandidateOutput, generate_id
from schemas.run import RunRecord
from schemas.decision import Decision
from schemas.probe import ProbePlan, ProbeResult
from schemas.trace import AuditTrace, NodeEvent
from db import RunsRepository


# Test client fixture
@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestReportMdGeneration:
    """Test server-side Markdown report generation."""

    def test_report_md_has_required_sections(self):
        """Generated report.md has all required sections."""
        run_record = {
            "run_id": "run_test_001",
            "version": "1.0.0",
            "created_at": "2026-01-26T10:00:00Z",
            "task_spec": {
                "description": "Test task",
                "constraints": ["Constraint 1"],
            },
            "candidate_output": {
                "content": "Test output",
            },
            "decision": {
                "verdict": "ACCEPT",
                "confidence": 0.95,
                "rationale": "Looks good",
            },
            "probe_plan": {
                "probes": [
                    {
                        "name": "Probe 1",
                        "description": "First probe",
                    }
                ]
            },
            "probe_results": [
                {
                    "probe_name": "Probe 1",
                    "verdict": "PASS",
                    "confidence": 0.9,
                    "rationale": "Passed",
                    "evidence": [],
                    "failure_labels": [],
                }
            ],
            "config_snapshot": {"model": "test"},
        }

        markdown = generate_report_md(run_record)

        # Verify all major sections are present
        assert "# Polaris Evaluation Run:" in markdown
        assert "## Summary" in markdown
        assert "## Task Specification" in markdown
        assert "## Candidate Output" in markdown
        assert "## Decision" in markdown
        assert "## Probe Plan" in markdown
        assert "## Probe Results" in markdown
        assert "## Configuration" in markdown

        # Verify content is present
        assert "run_test_001" in markdown
        assert "Test task" in markdown
        assert "ACCEPT" in markdown
        assert "0.95" in markdown

    def test_report_md_with_evidence(self):
        """Report includes evidence from probe results."""
        run_record = {
            "run_id": "run_evidence_001",
            "created_at": "2026-01-26T10:00:00Z",
            "task_spec": {"description": "Test"},
            "candidate_output": {"content": "Test"},
            "decision": None,
            "probe_results": [
                {
                    "probe_name": "Test Probe",
                    "verdict": "FAIL",
                    "confidence": 0.85,
                    "rationale": "Found issue",
                    "evidence": [
                        {
                            "type": "comparison",
                            "source": "test",
                            "content": "Expected: A\nGot: B",
                        }
                    ],
                    "failure_labels": ["label1", "label2"],
                }
            ],
            "config_snapshot": {},
        }

        markdown = generate_report_md(run_record)

        assert "Evidence:" in markdown
        assert "comparison" in markdown
        assert "Expected: A" in markdown
        assert "Failure Labels:" in markdown
        assert "label1, label2" in markdown

    def test_report_md_without_optional_fields(self):
        """Report handles missing optional fields gracefully."""
        minimal_record = {
            "run_id": "run_minimal_001",
            "created_at": "2026-01-26T10:00:00Z",
            "task_spec": {"description": "Minimal task"},
            "candidate_output": {"content": "Minimal output"},
        }

        markdown = generate_report_md(minimal_record)

        assert "Polaris Evaluation Run:" in markdown
        assert "No decision available" in markdown
        assert "Minimal task" in markdown


class TestRunsListPage:
    """Test /runs page rendering."""

    def test_runs_list_page_renders(self, client):
        """GET /runs returns 200 and renders page."""
        response = client.get("/runs")
        assert response.status_code == 200
        assert b"Evaluation Runs" in response.content
        assert b"Run ID" in response.content
        assert b"Status" in response.content

    def test_runs_list_with_pagination_params(self, client):
        """Pagination params are accepted."""
        response = client.get("/runs?limit=25&offset=0")
        assert response.status_code == 200

    def test_runs_list_with_status_filter(self, client):
        """Status filter param works."""
        response = client.get("/runs?status=COMPLETED")
        assert response.status_code == 200

    def test_runs_list_shows_filter_badges(self, client):
        """Filter badges are rendered on page."""
        response = client.get("/runs")
        assert response.status_code == 200
        assert b"QUEUED" in response.content
        assert b"RUNNING" in response.content
        assert b"COMPLETED" in response.content
        assert b"FAILED" in response.content


class TestRunDetailPage:
    """Test /runs/{id} page rendering."""

    async def test_run_detail_page_renders(
        self, client, db_conn: AsyncConnection, task_spec, candidate_output
    ):
        """GET /runs/{id} renders run detail page."""
        run_id = generate_id("run")

        # Create a run in the database
        await RunsRepository.create_run(
            db_conn,
            run_id,
            task_spec.model_dump(),
            candidate_output.model_dump(),
        )

        response = client.get(f"/runs/{run_id}")
        assert response.status_code == 200
        assert run_id.encode() in response.content
        assert b"Task Specification" in response.content
        assert b"Candidate Output" in response.content

    def test_run_detail_404_for_nonexistent(self, client):
        """Non-existent run returns 404."""
        response = client.get("/runs/run_nonexistent_12345")
        assert response.status_code == 404

    async def test_run_detail_shows_decision(
        self, client, db_conn: AsyncConnection, task_spec, candidate_output
    ):
        """Completed run displays decision."""
        run_id = generate_id("run")

        # Create run with decision
        run_record = {
            "version": "1.0.0",
            "run_id": run_id,
            "task_spec": task_spec.model_dump(),
            "candidate_output": candidate_output.model_dump(),
            "probe_plan": None,
            "probe_results": [],
            "decision": {
                "verdict": "ACCEPT",
                "confidence": 0.95,
                "rationale": "Test decision",
                "required_changes": [],
            },
            "audit_trace": None,
            "config_snapshot": {},
            "created_at": "2026-01-26T10:00:00Z",
        }

        await RunsRepository.create_run(
            db_conn,
            run_id,
            task_spec.model_dump(),
            candidate_output.model_dump(),
        )

        # Mock update to add run_record
        async with db_conn.cursor() as cur:
            await cur.execute(
                "UPDATE runs SET run_record = %s WHERE run_id = %s",
                (json.dumps(run_record), run_id),
            )
        await db_conn.commit()

        response = client.get(f"/runs/{run_id}")
        assert response.status_code == 200
        assert b"ACCEPT" in response.content
        assert b"0.95" in response.content


class TestAPIRunsListEndpoint:
    """Test GET /api/runs endpoint."""

    async def test_api_runs_list_endpoint(self, client):
        """GET /api/runs returns JSON with pagination."""
        response = client.get("/api/runs?limit=10&offset=0")
        assert response.status_code == 200

        data = response.json()
        assert "runs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_api_runs_list_default_params(self, client):
        """Default pagination parameters work."""
        response = client.get("/api/runs")
        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 50
        assert data["offset"] == 0

    def test_api_runs_list_limit_capped(self, client):
        """Limit is capped at 100."""
        response = client.get("/api/runs?limit=200")
        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 100

    def test_api_runs_list_invalid_limit(self, client):
        """Invalid limit returns error."""
        response = client.get("/api/runs?limit=0")
        assert response.status_code == 400

    def test_api_runs_list_invalid_offset(self, client):
        """Invalid offset returns error."""
        response = client.get("/api/runs?offset=-1")
        assert response.status_code == 400


class TestAPIReportMdEndpoint:
    """Test GET /api/runs/{id}/report.md endpoint."""

    async def test_report_md_endpoint_success(
        self, client, db_conn: AsyncConnection, task_spec, candidate_output
    ):
        """GET /api/runs/{id}/report.md returns Markdown."""
        run_id = generate_id("run")

        # Create run with record
        run_record = {
            "version": "1.0.0",
            "run_id": run_id,
            "task_spec": task_spec.model_dump(),
            "candidate_output": candidate_output.model_dump(),
            "decision": {
                "verdict": "ACCEPT",
                "confidence": 0.95,
                "rationale": "Test",
                "required_changes": [],
            },
            "probe_plan": None,
            "probe_results": [],
            "audit_trace": None,
            "config_snapshot": {},
            "created_at": "2026-01-26T10:00:00Z",
        }

        await RunsRepository.create_run(
            db_conn,
            run_id,
            task_spec.model_dump(),
            candidate_output.model_dump(),
        )

        async with db_conn.cursor() as cur:
            await cur.execute(
                "UPDATE runs SET run_record = %s WHERE run_id = %s",
                (json.dumps(run_record), run_id),
            )
        await db_conn.commit()

        response = client.get(f"/api/runs/{run_id}/report.md")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
        assert b"Polaris Evaluation Run:" in response.content
        assert b"ACCEPT" in response.content

    def test_report_md_endpoint_404(self, client):
        """Non-existent run returns 404."""
        response = client.get("/api/runs/run_nonexistent/report.md")
        assert response.status_code == 404

    async def test_report_md_endpoint_incomplete(
        self, client, db_conn: AsyncConnection, task_spec, candidate_output
    ):
        """Incomplete run returns 202."""
        run_id = generate_id("run")

        await RunsRepository.create_run(
            db_conn,
            run_id,
            task_spec.model_dump(),
            candidate_output.model_dump(),
        )

        response = client.get(f"/api/runs/{run_id}/report.md")
        assert response.status_code == 202


class TestIndexRedirect:
    """Test / index route."""

    def test_index_redirects_to_runs(self, client):
        """GET / redirects to /runs."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/runs"
