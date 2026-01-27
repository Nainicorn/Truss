"""Tests for FastAPI endpoints - simplified unit tests."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
import pytest

from apps.api import app, _hash_payload
from schemas import TaskSpec, CandidateOutput


@pytest.fixture
def task_spec():
    """Example TaskSpec for tests."""
    return TaskSpec(
        task_id="task_test_001",
        description="Test task",
        constraints=["Must mention health"],
        allowed_tools=None,
        domain_tags=["health"],
        rubric_id=None,
    )


@pytest.fixture
def candidate_output():
    """Example CandidateOutput for tests."""
    return CandidateOutput(
        candidate_id="cand_test_001",
        content="This is about health and wellness.",
        tool_calls=[],
        metadata={},
    )


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test /health endpoint (no dependencies)."""

    def test_health_check(self, client):
        """GET /health returns ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestAPIKeyValidation:
    """Test API key validation."""

    async def test_validate_api_key_function(self):
        """Test API key validation function directly."""
        from apps.api import validate_api_key
        from fastapi import HTTPException
        import pytest

        # Valid key should not raise
        result = await validate_api_key("dev-key-12345")
        assert result == "dev-key-12345"

        # Invalid key should raise 403
        with pytest.raises(HTTPException) as exc_info:
            await validate_api_key("invalid-key")
        assert exc_info.value.status_code == 403


class TestIdempotencyHashing:
    """Test idempotency payload hashing."""

    def test_idempotency_hash_consistency(self, task_spec, candidate_output):
        """Hash of same payload is consistent."""
        hash1 = _hash_payload(task_spec, candidate_output)
        hash2 = _hash_payload(task_spec, candidate_output)

        # Same payload → same hash
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256

    def test_idempotency_hash_differs_on_change(self, task_spec, candidate_output):
        """Hash differs when payload changes."""
        hash1 = _hash_payload(task_spec, candidate_output)

        # Modify content
        candidate_output.content = "Different content"
        hash2 = _hash_payload(task_spec, candidate_output)

        # Different payload → different hash
        assert hash1 != hash2


class TestRunIDGeneration:
    """Test run ID generation."""

    def test_run_id_format(self):
        """Run IDs have correct format."""
        from schemas import generate_id

        run_id = generate_id("run")
        assert run_id.startswith("run_")
        assert len(run_id) > 4

    def test_run_ids_are_unique(self):
        """Generated run IDs are unique."""
        from schemas import generate_id

        run_ids = {generate_id("run") for _ in range(100)}
        assert len(run_ids) == 100  # All unique
