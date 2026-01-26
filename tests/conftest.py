"""Shared test fixtures and configuration."""

import pytest

from schemas import utc_now


@pytest.fixture
def now():
    """Current UTC datetime."""
    return utc_now()
