"""RQ worker for executing evaluation runs."""

from rq import Worker, Queue
import redis
import structlog

from config import settings
from db import get_sync_connection, RunsRepository
from graphs import create_graph
from schemas.run import RunRecord

logger = structlog.get_logger()


def execute_run(run_id: str) -> str:
    """RQ task: Execute evaluation run.

    1. Load task_spec + candidate_output from DB
    2. Update status to RUNNING
    3. Execute graph (reuse create_graph())
    4. Store run_record, set status COMPLETED
    5. On error: set FAILED, store error text

    Args:
        run_id: Run identifier

    Returns:
        run_id on success

    Raises:
        Exception: If graph execution or DB update fails
    """
    conn = get_sync_connection(settings.database_url)
    logger.info("execute_run_started", run_id=run_id)

    try:
        # Load run inputs
        run_data = RunsRepository.get_run_sync(conn, run_id)
        if not run_data:
            raise ValueError(f"Run {run_id} not found in database")

        task_spec_dict = run_data["task_spec"]
        candidate_output_dict = run_data["candidate_output"]

        # Update status to RUNNING
        RunsRepository.update_status_running(conn, run_id)
        logger.info("run_status_updated", run_id=run_id, status="RUNNING")

        # Execute graph (Phase 2 reuse)
        graph = create_graph()
        state = graph.invoke({
            "task_spec": task_spec_dict,
            "candidate_output": candidate_output_dict,
        })

        # Extract RunRecord from final state
        run_record = RunRecord.model_validate(state["run_record"])
        logger.info(
            "graph_executed",
            run_id=run_id,
            verdict=run_record.decision.verdict,
            probe_count=len(run_record.probe_results),
        )

        # Store run_record and set status COMPLETED
        RunsRepository.update_completed(conn, run_id, run_record.model_dump(mode='json'))
        logger.info("run_completed", run_id=run_id, verdict=run_record.decision.verdict)

        return run_id

    except Exception as e:
        logger.exception("run_failed", run_id=run_id, error=str(e))
        error_msg = f"{type(e).__name__}: {str(e)}"
        RunsRepository.update_failed(conn, run_id, error_msg)
        raise

    finally:
        conn.close()


def start_worker() -> None:
    """Start RQ worker.

    Listens on the configured queue and executes jobs.
    """
    redis_conn = redis.from_url(settings.worker_redis_url)

    logger.info(
        "worker_starting",
        queue=settings.rq_queue_name,
        redis_url=settings.worker_redis_url,
    )

    worker = Worker([settings.rq_queue_name], connection=redis_conn)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    start_worker()
