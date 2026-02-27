from __future__ import annotations

import os
import tempfile
import pytest

from backend.app.config import settings
from backend.app.database import get_connection, init_db


@pytest.fixture(autouse=True)
def test_database(tmp_path):
    """Set up a temporary database for every test that hits the API."""
    db_path = str(tmp_path / "test.db")
    original_url = settings.DATABASE_URL
    settings.DATABASE_URL = f"sqlite:///{db_path}"

    conn = get_connection(db_path)
    init_db(conn)
    conn.close()

    yield db_path

    settings.DATABASE_URL = original_url
