"""FastAPI service for Polaris evaluation runs."""

import hashlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Header
from psycopg import AsyncConnection
import redis.asyncio as redis
from rq import Queue
import structlog

from config import settings
from db import init_db_pool, close_db_pool, get_db, RunsRepository
from schemas import TaskSpec, CandidateOutput, generate_id
from utils import init_redis, get_redis, close_redis, IdempotencyManager, RateLimiter

logger = structlog.get_logger()


# Lifespan: manage connections
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    await init_db_pool(settings.database_url)
    await init_redis(settings.redis_url)
    logger.info("services_initialized", db_url=settings.database_url, redis_url=settings.redis_url)
    yield
    await close_db_pool()
    await close_redis()
    logger.info("services_closed")


app = FastAPI(
    title="Polaris Evaluation API",
    version="0.3.0",
    lifespan=lifespan,
)


# Dependency: API key validation
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


# Dependency: rate limiting
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


def _hash_payload(task_spec: TaskSpec, candidate: CandidateOutput) -> str:
    """Hash payload for idempotency comparison.

    Args:
        task_spec: Task specification
        candidate: Candidate output

    Returns:
        SHA256 hash of concatenated model dumps
    """
    content = task_spec.model_dump_json() + candidate.model_dump_json()
    return hashlib.sha256(content.encode()).hexdigest()


@app.post("/api/runs", status_code=202)
async def create_run(
    task_spec: TaskSpec,
    candidate_output: CandidateOutput,
    conn: AsyncConnection = Depends(get_db),
    api_key: str = Depends(check_rate_limit),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict:
    """Create evaluation run, enqueue job, return run_id.

    POST /api/runs
    Content-Type: application/json
    X-API-Key: dev-key-12345
    Idempotency-Key: optional-unique-key

    Request body:
    {
      "task_spec": {...},
      "candidate_output": {...}
    }

    Returns:
    {
      "run_id": "run_abc123...",
      "status": "QUEUED",
      "created_at": "2026-01-26T..."
    }

    Args:
        task_spec: Task specification (validated by Pydantic)
        candidate_output: Candidate output (validated by Pydantic)
        conn: Database connection
        api_key: Validated API key
        idempotency_key: Optional header for idempotency

    Returns:
        dict with run_id, status, created_at

    Raises:
        HTTPException: 400 if validation fails, 429 if rate limited
    """
    payload_hash = _hash_payload(task_spec, candidate_output)

    # Check idempotency (DB-first)
    if idempotency_key:
        existing_run_id = await RunsRepository.check_idempotency(
            conn, idempotency_key, payload_hash
        )
        if existing_run_id:
            logger.info("idempotency_hit", run_id=existing_run_id, idempotency_key=idempotency_key)
            return {
                "run_id": existing_run_id,
                "status": "QUEUED",
            }

    # Create new run
    run_id = generate_id("run")
    await RunsRepository.create_run(
        conn,
        run_id,
        task_spec.model_dump(),
        candidate_output.model_dump(),
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
    )

    # Enqueue job (RQ)
    try:
        redis_conn = redis.from_url(settings.redis_url)
        queue = Queue(settings.rq_queue_name, connection=redis_conn)
        job = queue.enqueue("apps.worker.execute_run", run_id, job_id=run_id)
        logger.info("run_queued", run_id=run_id, job_id=job.id)
    except Exception as e:
        logger.exception("queue_failed", run_id=run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to enqueue job") from e

    # Cache idempotency in Redis (for performance)
    if idempotency_key:
        try:
            idempotency = IdempotencyManager(get_redis())
            await idempotency.set(idempotency_key, payload_hash, run_id)
        except Exception as e:
            logger.warning("idempotency_cache_failed", run_id=run_id, error=str(e))

    return {
        "run_id": run_id,
        "status": "QUEUED",
    }


@app.get("/api/runs/{run_id}")
async def get_run_status(
    run_id: str,
    conn: AsyncConnection = Depends(get_db),
) -> dict:
    """Get run status and optional decision summary.

    GET /api/runs/{run_id}

    Returns:
    {
      "run_id": "run_abc123...",
      "status": "COMPLETED",
      "created_at": "2026-01-26T...",
      "updated_at": "2026-01-26T...",
      "decision": {"verdict": "ACCEPT", "confidence": 0.95} or null
    }

    Args:
        run_id: Run identifier
        conn: Database connection

    Returns:
        dict with run status and decision (if completed)

    Raises:
        HTTPException: 404 if run not found
    """
    run = await RunsRepository.get_run(conn, run_id)
    if not run:
        logger.warning("run_not_found", run_id=run_id)
        raise HTTPException(status_code=404, detail="Run not found")

    summary = {
        "run_id": run["run_id"],
        "status": run["status"],
        "created_at": run["created_at"].isoformat() if run["created_at"] else None,
        "updated_at": run["updated_at"].isoformat() if run["updated_at"] else None,
        "decision": None,
    }

    if run["run_record"]:
        summary["decision"] = run["run_record"].get("decision")

    return summary


@app.get("/api/runs/{run_id}/record")
async def get_run_record(
    run_id: str,
    conn: AsyncConnection = Depends(get_db),
) -> dict:
    """Get full RunRecord JSON.

    GET /api/runs/{run_id}/record

    Returns full RunRecord if COMPLETED, else 202 Accepted with status.

    Args:
        run_id: Run identifier
        conn: Database connection

    Returns:
        RunRecord dict if completed

    Raises:
        HTTPException: 404 if run not found, 202 if incomplete
    """
    run = await RunsRepository.get_run(conn, run_id)
    if not run:
        logger.warning("run_not_found", run_id=run_id)
        raise HTTPException(status_code=404, detail="Run not found")

    if not run["run_record"]:
        logger.info("run_not_complete", run_id=run_id, status=run["status"])
        return {
            "run_id": run_id,
            "status": run["status"],
            "message": f"Run not yet completed (status: {run['status']})",
        }

    return run["run_record"]


@app.get("/api/runs/{run_id}/trace")
async def get_audit_trace(
    run_id: str,
    conn: AsyncConnection = Depends(get_db),
) -> dict:
    """Get AuditTrace only (from RunRecord.audit_trace).

    GET /api/runs/{run_id}/trace

    Returns AuditTrace if COMPLETED, else 202 Accepted with status.

    Args:
        run_id: Run identifier
        conn: Database connection

    Returns:
        AuditTrace dict if completed

    Raises:
        HTTPException: 404 if run not found, 202 if incomplete
    """
    run = await RunsRepository.get_run(conn, run_id)
    if not run:
        logger.warning("run_not_found", run_id=run_id)
        raise HTTPException(status_code=404, detail="Run not found")

    if not run["run_record"] or "audit_trace" not in run["run_record"]:
        logger.info("trace_not_available", run_id=run_id, status=run["status"])
        return {
            "run_id": run_id,
            "status": run["status"],
            "message": f"Trace not available (status: {run['status']})",
        }

    return run["run_record"]["audit_trace"]


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        dict with status
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
