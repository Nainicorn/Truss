"""Rate limiting via Redis fixed-window counter."""

import time

import redis.asyncio as redis


class RateLimiter:
    """Fixed-window rate limiter using Redis."""

    def __init__(self, redis_client: redis.Redis):
        """Initialize with Redis client.

        Args:
            redis_client: Async Redis client
        """
        self.redis = redis_client

    async def check(self, api_key: str, limit: int, window: int) -> bool:
        """Check if request is allowed (fixed window).

        Args:
            api_key: API key to rate limit
            limit: Max requests per window
            window: Window duration in seconds

        Returns:
            True if request allowed, False if rate limit exceeded
        """
        # Fixed window: current_timestamp // window_size
        window_key = int(time.time() // window)
        key = f"rate_limit:{api_key}:{window_key}"

        # Increment counter
        current = await self.redis.incr(key)

        # Set expiration only on first increment
        if current == 1:
            await self.redis.expire(key, window)

        return current <= limit
