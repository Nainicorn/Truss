"""Shared test fixtures and configuration."""

import asyncio
import json

import psycopg
from psycopg_pool import AsyncConnectionPool
import pytest
import redis
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from schemas import utc_now


@pytest.fixture
def now():
    """Current UTC datetime."""
    return utc_now()


# Testcontainer fixtures for Phase 3 tests


@pytest.fixture(scope="session")
def postgres_container():
    """Start Postgres testcontainer for entire test session.

    Yields:
        PostgresContainer instance
    """
    with PostgresContainer("postgres:16-alpine") as postgres:
        # Initialize schema
        conn_url = postgres.get_connection_url()
        conn = psycopg.connect(conn_url)
        with open("db/init.sql") as f:
            conn.execute(f.read())
        conn.commit()
        conn.close()
        yield postgres


@pytest.fixture(scope="session")
def redis_container():
    """Start Redis testcontainer for entire test session.

    Yields:
        RedisContainer instance
    """
    with RedisContainer("redis:7-alpine") as redis_c:
        yield redis_c


@pytest.fixture
async def db_pool(postgres_container):
    """Async DB connection pool for tests.

    Yields:
        AsyncConnectionPool instance
    """
    pool = AsyncConnectionPool(
        conninfo=postgres_container.get_connection_url(),
        min_size=2,
        max_size=5,
    )
    await pool.wait()
    yield pool
    await pool.close()


@pytest.fixture
async def db_conn(db_pool):
    """Async DB connection for tests.

    Yields:
        AsyncConnection instance
    """
    async with db_pool.connection() as conn:
        yield conn


@pytest.fixture
def redis_client(redis_container):
    """Redis client for tests.

    Yields:
        redis.Redis instance
    """
    client = redis.from_url(redis_container.get_connection_url(), decode_responses=True)
    yield client
    client.close()


@pytest.fixture
def sync_db_conn(postgres_container):
    """Synchronous DB connection for worker tests.

    Yields:
        psycopg Connection instance
    """
    conn = psycopg.connect(postgres_container.get_connection_url())
    yield conn
    conn.close()
