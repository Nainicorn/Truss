"""Tests for RQ worker - simplified unit tests."""

from unittest.mock import MagicMock, patch

import pytest

from server.worker import execute_run
from schemas import TaskSpec, CandidateOutput, generate_id


@pytest.fixture
def task_spec():
    """Example TaskSpec for tests."""
    return TaskSpec(
        task_id="task_worker_test_001",
        description="Worker test task",
        constraints=["Must be valid"],
        allowed_tools=None,
        domain_tags=["test"],
        rubric_id=None,
    )


@pytest.fixture
def candidate_output():
    """Example CandidateOutput for tests."""
    return CandidateOutput(
        candidate_id="cand_worker_test_001",
        content="This is valid content that should pass.",
        tool_calls=[],
        metadata={},
    )


class TestWorkerDBInteraction:
    """Test worker database interactions."""

    def test_worker_loads_run_from_db(self, task_spec, candidate_output):
        """Worker loads task and candidate from database by run_id."""
        run_id = generate_id("run")

        with patch("apps.worker.get_sync_connection") as mock_get_conn, \
             patch("apps.worker.RunsRepository.get_run_sync") as mock_get_run, \
             patch("apps.worker.RunsRepository.update_status_running"), \
             patch("apps.worker.create_graph") as mock_create_graph, \
             patch("apps.worker.RunsRepository.update_completed"):

            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            mock_get_run.return_value = {
                "task_spec": task_spec.model_dump(),
                "candidate_output": candidate_output.model_dump(),
            }

            # Execute worker (will fail on graph, but we verify the DB load)
            try:
                execute_run(run_id)
            except:
                pass  # Expected to fail on graph execution

            # Verify DB load was called
            mock_get_run.assert_called_once_with(mock_conn, run_id)

    def test_worker_raises_if_run_not_found(self):
        """Worker raises error if run not found in database."""
        run_id = generate_id("run")

        with patch("apps.worker.get_sync_connection") as mock_get_conn, \
             patch("apps.worker.RunsRepository.get_run_sync") as mock_get_run:

            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            mock_get_run.return_value = None

            # Should raise ValueError
            with pytest.raises(ValueError, match="not found"):
                execute_run(run_id)


class TestWorkerErrorHandling:
    """Test worker error handling."""

    def test_worker_updates_running_status(self, task_spec, candidate_output):
        """Worker updates status to RUNNING at start."""
        run_id = generate_id("run")

        with patch("apps.worker.get_sync_connection") as mock_get_conn, \
             patch("apps.worker.RunsRepository.get_run_sync") as mock_get_run, \
             patch("apps.worker.RunsRepository.update_status_running") as mock_update_running, \
             patch("apps.worker.create_graph") as mock_create_graph:

            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            mock_get_run.return_value = {
                "task_spec": task_spec.model_dump(),
                "candidate_output": candidate_output.model_dump(),
            }

            # Make graph fail so we can verify status update was called before error
            mock_create_graph.return_value.invoke.side_effect = Exception("Graph error")

            try:
                execute_run(run_id)
            except:
                pass

            # Verify update_running was called
            mock_update_running.assert_called_once_with(mock_conn, run_id)

    def test_worker_handles_graph_error(self, task_spec, candidate_output):
        """Worker catches and logs graph execution errors."""
        run_id = generate_id("run")

        with patch("apps.worker.get_sync_connection") as mock_get_conn, \
             patch("apps.worker.RunsRepository.get_run_sync") as mock_get_run, \
             patch("apps.worker.RunsRepository.update_status_running"), \
             patch("apps.worker.create_graph") as mock_create_graph, \
             patch("apps.worker.RunsRepository.update_failed") as mock_update_failed:

            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            mock_get_run.return_value = {
                "task_spec": task_spec.model_dump(),
                "candidate_output": candidate_output.model_dump(),
            }
            mock_create_graph.return_value.invoke.side_effect = Exception("Graph error")

            # Should raise and update failed
            with pytest.raises(Exception):
                execute_run(run_id)

            # Verify update_failed was called with error message
            mock_update_failed.assert_called_once()
            call_args = mock_update_failed.call_args[0]
            assert call_args[0] == mock_conn
            assert call_args[1] == run_id
            assert "Graph error" in call_args[2]  # error message


class TestWorkerGraphReuse:
    """Test worker reuses Phase 2 graph."""

    def test_worker_imports_create_graph_from_phase2(self):
        """Worker imports create_graph from Phase 2 graphs module."""
        from apps.worker import create_graph
        from graphs import create_graph as phase2_create_graph

        # Both should be the same
        assert create_graph == phase2_create_graph

    def test_worker_imports_runrecord_schema(self):
        """Worker imports RunRecord from Phase 1 schemas."""
        from apps.worker import RunRecord
        from schemas.run import RunRecord as phase1_runrecord

        assert RunRecord == phase1_runrecord
