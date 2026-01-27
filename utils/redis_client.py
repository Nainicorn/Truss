"""Redis client singleton for async use."""

import redis.asyncio as redis

_redis_client: redis.Redis | None = None


async def init_redis(redis_url: str) -> None:
    """Initialize Redis client.

    Args:
        redis_url: Redis connection URL
    """
    global _redis_client
    _redis_client = redis.from_url(redis_url, decode_responses=True)


def get_redis() -> redis.Redis:
    """Get Redis client instance.

    Returns:
        Redis async client

    Raises:
        RuntimeError: If client not initialized
    """
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() first.")
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
