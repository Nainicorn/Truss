"""FastAPI dependency injection: authentication and rate limiting."""

import hashlib

from fastapi import Depends, HTTPException, Header
import structlog

from config import settings
from schemas import TaskSpec, CandidateOutput
from .services.redis import get_redis
from .middleware.rate_limit import RateLimiter

logger = structlog.get_logger()


async def validate_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Validate API key and return it.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        API key

    Raises:
        HTTPException: 403 if invalid API key
    """
    if x_api_key not in settings.api_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


async def check_rate_limit(
    api_key: str = Depends(validate_api_key),
) -> str:
    """Rate limit: 10 req/min per API key.

    Args:
        api_key: Validated API key

    Returns:
        API key if allowed

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    limiter = RateLimiter(get_redis())
    allowed = await limiter.check(api_key, limit=settings.rate_limit_per_minute, window=60)
    if not allowed:
        logger.warning("rate_limit_exceeded", api_key=api_key)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return api_key


def hash_payload(task_spec: TaskSpec, candidate: CandidateOutput) -> str:
    """Hash payload for idempotency comparison.

    Args:
        task_spec: Task specification
        candidate: Candidate output

    Returns:
        SHA256 hash of concatenated model dumps
    """
    content = task_spec.model_dump_json() + candidate.model_dump_json()
    return hashlib.sha256(content.encode()).hexdigest()
