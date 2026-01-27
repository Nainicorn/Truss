"""CLI for replaying a Polaris evaluation run."""

import argparse
import json
import sys

import redis
from rq import Queue
import structlog

from config import settings
from db import get_sync_connection, RunsRepository
from schemas import generate_id

logger = structlog.get_logger()


def main() -> int:
    """Replay a run.

    Command:
        python -m apps.replay_run --run-id <original_run_id>

    Returns:
        0 on success, 1 on error
    """
    parser = argparse.ArgumentParser(description="Replay a Polaris evaluation run")
    parser.add_argument("--run-id", required=True, help="Original run ID to replay")
    args = parser.parse_args()

    original_run_id = args.run_id
    conn = get_sync_connection(settings.database_url)

    try:
        # Load original run
        original_run = RunsRepository.get_run_sync(conn, original_run_id)
        if not original_run:
            print(f"Error: Run {original_run_id} not found", file=sys.stderr)
            logger.warning("replay_failed_not_found", run_id=original_run_id)
            return 1

        task_spec = original_run["task_spec"]
        candidate_output = original_run["candidate_output"]

        # Create new run
        new_run_id = generate_id("run")
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO runs (run_id, status, task_spec, candidate_output, replay_of)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    new_run_id,
                    "QUEUED",
                    json.dumps(task_spec),
                    json.dumps(candidate_output),
                    original_run_id,
                ),
            )
        conn.commit()

        logger.info("replay_run_created", new_run_id=new_run_id, original_run_id=original_run_id)

        # Enqueue job
        redis_conn = redis.from_url(settings.redis_url)
        queue = Queue(settings.rq_queue_name, connection=redis_conn)
        job = queue.enqueue("server.worker.execute_run", new_run_id, job_id=new_run_id)

        logger.info("replay_job_enqueued", new_run_id=new_run_id, job_id=job.id)

        print(f"Replay created: {new_run_id} (original: {original_run_id})")
        return 0

    except Exception as e:
        logger.exception("replay_error", run_id=original_run_id, error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1

    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
