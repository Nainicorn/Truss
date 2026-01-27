"""PostgreSQL connection pools and dependency injection."""

from psycopg_pool import AsyncConnectionPool
import psycopg

# Async pool for FastAPI endpoints
_async_pool: AsyncConnectionPool | None = None


async def init_db_pool(db_url: str) -> None:
    """Initialize async connection pool for FastAPI."""
    global _async_pool
    _async_pool = AsyncConnectionPool(
        conninfo=db_url,
        min_size=2,
        max_size=10,
        timeout=30.0,
    )
    await _async_pool.wait()


async def close_db_pool() -> None:
    """Close async pool on shutdown."""
    global _async_pool
    if _async_pool:
        await _async_pool.close()
        _async_pool = None


async def get_db():
    """Async dependency injection for FastAPI endpoints.

    Usage in FastAPI:
        @app.get("/runs/{run_id}")
        async def get_run(run_id: str, conn: AsyncConnection = Depends(get_db)):
            ...
    """
    if not _async_pool:
        raise RuntimeError("DB pool not initialized. Call init_db_pool() first.")

    async with _async_pool.connection() as conn:
        yield conn


def get_sync_connection(db_url: str):
    """Get synchronous connection for RQ worker.

    Args:
        db_url: PostgreSQL connection URL

    Returns:
        Synchronous psycopg Connection

    Usage in RQ worker:
        conn = get_sync_connection(settings.database_url)
        try:
            # Use conn for CRUD operations
        finally:
            conn.close()
    """
    return psycopg.connect(db_url)
