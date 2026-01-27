"""FastAPI router for evaluation runs API endpoints."""

import redis
import redis.asyncio as redis_async
from fastapi import APIRouter, Depends, HTTPException, Header
from psycopg import AsyncConnection
from rq import Queue
import structlog

from config import settings
from db import get_db, RunsRepository
from schemas import TaskSpec, CandidateOutput, generate_id
from .services.redis import get_redis
from .middleware.idempotency import IdempotencyManager
from .dependencies import check_rate_limit, hash_payload
from .report_generator import generate_report_md

logger = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["runs"])


@router.post("/runs", status_code=202)
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
    payload_hash = hash_payload(task_spec, candidate_output)

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
        task_spec.model_dump(mode='json'),
        candidate_output.model_dump(mode='json'),
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
    )

    # Enqueue job (RQ)
    try:
        redis_conn = redis.from_url(settings.redis_url)
        queue = Queue(settings.rq_queue_name, connection=redis_conn)
        job = queue.enqueue("server.worker.execute_run", run_id, job_id=run_id)
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


@router.get("/runs/{run_id}")
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


@router.get("/runs/{run_id}/record")
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


@router.get("/runs/{run_id}/trace")
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


@router.get("/runs")
async def list_runs(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    conn: AsyncConnection = Depends(get_db),
) -> dict:
    """List runs with pagination.

    GET /api/runs?limit=50&offset=0&status=COMPLETED

    Args:
        limit: Max results per page (default 50, max 100)
        offset: Pagination offset (default 0)
        status: Optional status filter (QUEUED, RUNNING, COMPLETED, FAILED)
        conn: Database connection

    Returns:
        dict with runs list, total count, pagination metadata

    Raises:
        HTTPException: 400 if invalid parameters
    """
    limit = min(limit, 100)  # Cap at 100
    if limit < 1:
        raise HTTPException(status_code=400, detail="limit must be >= 1")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")

    runs = await RunsRepository.list_runs(conn, limit, offset, status)
    total = await RunsRepository.count_runs(conn, status)

    logger.info(
        "runs_listed",
        limit=limit,
        offset=offset,
        status=status,
        count=len(runs),
        total=total,
    )

    return {
        "runs": runs,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/runs/{run_id}/report.md")
async def get_report_md(
    run_id: str,
    conn: AsyncConnection = Depends(get_db),
):
    """Generate Markdown report for completed run.

    GET /api/runs/{run_id}/report.md

    Returns:
        Plain text Markdown file with Content-Disposition header for download

    Raises:
        HTTPException: 404 if run not found, 202 if incomplete
    """
    from fastapi.responses import Response

    run = await RunsRepository.get_run(conn, run_id)
    if not run:
        logger.warning("run_not_found_for_report", run_id=run_id)
        raise HTTPException(status_code=404, detail="Run not found")

    if not run["run_record"]:
        logger.info("run_incomplete_for_report", run_id=run_id, status=run["status"])
        raise HTTPException(
            status_code=202,
            detail=f"Run not yet completed (status: {run['status']})",
        )

    markdown = generate_report_md(run["run_record"])

    return Response(
        content=markdown,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=polaris-run-{run_id}.md"
        },
    )
