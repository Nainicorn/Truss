"""Idempotency key management via Redis cache (DB is source of truth)."""

import redis.asyncio as redis


class IdempotencyManager:
    """Manage idempotency keys with Redis caching."""

    def __init__(self, redis_client: redis.Redis):
        """Initialize with Redis client.

        Args:
            redis_client: Async Redis client
        """
        self.redis = redis_client

    def _key(self, idempotency_key: str, payload_hash: str) -> str:
        """Generate Redis key for idempotency mapping.

        Args:
            idempotency_key: Client-provided idempotency key
            payload_hash: SHA256 hash of request payload

        Returns:
            Redis key
        """
        return f"idempotency:{idempotency_key}:{payload_hash}"

    async def get(self, idempotency_key: str, payload_hash: str) -> str | None:
        """Get cached run_id from Redis (if exists).

        Note: DB query is done in the API layer before checking cache.
        This is a fallback cache for performance.

        Args:
            idempotency_key: Client-provided idempotency key
            payload_hash: SHA256 hash of request payload

        Returns:
            Cached run_id or None
        """
        key = self._key(idempotency_key, payload_hash)
        value = await self.redis.get(key)
        return value

    async def set(
        self,
        idempotency_key: str,
        payload_hash: str,
        run_id: str,
        ttl: int = 86400,
    ) -> None:
        """Cache run_id in Redis (24h default TTL).

        Args:
            idempotency_key: Client-provided idempotency key
            payload_hash: SHA256 hash of request payload
            run_id: Run ID to cache
            ttl: Time to live in seconds (default 24h)
        """
        key = self._key(idempotency_key, payload_hash)
        await self.redis.setex(key, ttl, run_id)
