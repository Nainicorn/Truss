"""FastAPI router for UI template rendering and static file serving."""

from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from psycopg import AsyncConnection
from fastapi import Depends
import structlog

from db import get_db, RunsRepository

logger = structlog.get_logger()

router = APIRouter(tags=["ui"])


def format_datetime(dt):
    """Format datetime for template display."""
    if dt is None:
        return "—"

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return str(dt)

    if not isinstance(dt, datetime):
        return str(dt)

    return dt.strftime('%Y-%m-%d %H:%M:%S')


# Initialize Jinja2 templates
templates = Jinja2Templates(directory="ui/templates")
templates.env.filters['format_datetime'] = format_datetime


@router.get("/")
async def index():
    """Redirect to /runs page."""
    return RedirectResponse(url="/runs")


@router.get("/runs")
async def runs_list_page(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    conn: AsyncConnection = Depends(get_db),
):
    """Render runs list page (HTML).

    GET /runs?limit=50&offset=0&status=COMPLETED

    Args:
        request: FastAPI Request object (required for templates)
        limit: Max results per page
        offset: Pagination offset
        status: Optional status filter
        conn: Database connection

    Returns:
        Rendered HTML template
    """
    limit = min(limit, 100)
    runs = await RunsRepository.list_runs(conn, limit, offset, status)
    total = await RunsRepository.count_runs(conn, status)

    current_page = (offset // limit) + 1 if limit > 0 else 1
    has_next = (offset + limit) < total
    has_prev = offset > 0

    logger.info("runs_page_rendered", limit=limit, offset=offset, status=status)

    return templates.TemplateResponse(
        "runs_list.html",
        {
            "request": request,
            "runs": runs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "status": status,
            "current_page": current_page,
            "next_offset": offset + limit if has_next else None,
            "prev_offset": max(0, offset - limit) if has_prev else None,
            "has_next": has_next,
            "has_prev": has_prev,
        },
    )


@router.get("/runs/{run_id}")
async def run_detail_page(
    run_id: str,
    request: Request,
    conn: AsyncConnection = Depends(get_db),
):
    """Render run detail page (HTML).

    GET /runs/{run_id}

    Args:
        run_id: Run identifier
        request: FastAPI Request object (required for templates)
        conn: Database connection

    Returns:
        Rendered HTML template or 404

    Raises:
        HTTPException: 404 if run not found
    """
    from fastapi import HTTPException

    run = await RunsRepository.get_run(conn, run_id)
    if not run:
        logger.warning("run_not_found_for_detail", run_id=run_id)
        raise HTTPException(status_code=404, detail="Run not found")

    # Extract fields for template
    run_record = run["run_record"] or {}
    template_context = {
        "request": request,
        "run_id": run["run_id"],
        "status": run["status"],
        "created_at": run["created_at"],
        "updated_at": run["updated_at"],
        "task_spec": run["task_spec"],
        "candidate_output": run["candidate_output"],
        "probe_plan": run_record.get("probe_plan"),
        "probe_results": run_record.get("probe_results", []),
        "decision": run_record.get("decision"),
        "audit_trace": run_record.get("audit_trace"),
    }

    logger.info("run_detail_page_rendered", run_id=run_id)

    return templates.TemplateResponse("run_detail.html", template_context)


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        dict with status
    """
    return {"status": "ok"}
