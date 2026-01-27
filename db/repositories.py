"""CRUD operations for runs table."""

import json
from typing import Any

from psycopg import AsyncConnection, Connection

from schemas.run import RunRecord


class RunsRepository:
    """Repository for runs table CRUD operations."""

    # Async methods for FastAPI endpoints

    @staticmethod
    async def create_run(
        conn: AsyncConnection,
        run_id: str,
        task_spec: dict,
        candidate_output: dict,
        idempotency_key: str | None = None,
        payload_hash: str | None = None,
        replay_of: str | None = None,
    ) -> None:
        """Insert new run with QUEUED status.

        Args:
            conn: Async database connection
            run_id: Unique run identifier
            task_spec: Task specification dict
            candidate_output: Candidate output dict
            idempotency_key: Optional idempotency key
            payload_hash: Optional payload hash for idempotency
            replay_of: Optional reference to original run_id
        """
        await conn.execute(
            """
            INSERT INTO runs (run_id, status, task_spec, candidate_output,
                            idempotency_key, payload_hash, replay_of)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                "QUEUED",
                json.dumps(task_spec),
                json.dumps(candidate_output),
                idempotency_key,
                payload_hash,
                replay_of,
            ),
        )

    @staticmethod
    async def get_run(conn: AsyncConnection, run_id: str) -> dict | None:
        """Fetch run by ID (returns dict, not Pydantic).

        Args:
            conn: Async database connection
            run_id: Run identifier

        Returns:
            Dict with keys: run_id, status, created_at, updated_at, task_spec,
            candidate_output, run_record, error, replay_of
        """
        cursor = await conn.execute(
            """
            SELECT run_id, status, created_at, updated_at, task_spec,
                   candidate_output, run_record, error, replay_of
            FROM runs WHERE run_id = %s
            """,
            (run_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return {
            "run_id": row[0],
            "status": row[1],
            "created_at": row[2],
            "updated_at": row[3],
            "task_spec": row[4] if isinstance(row[4], dict) else json.loads(row[4]),
            "candidate_output": row[5] if isinstance(row[5], dict) else json.loads(row[5]),
            "run_record": row[6] if isinstance(row[6], dict) else (json.loads(row[6]) if row[6] else None),
            "error": row[7],
            "replay_of": row[8],
        }

    @staticmethod
    async def get_run_record(conn: AsyncConnection, run_id: str) -> RunRecord | None:
        """Fetch complete RunRecord (validates Pydantic).

        Args:
            conn: Async database connection
            run_id: Run identifier

        Returns:
            RunRecord instance or None if not found or not completed
        """
        cursor = await conn.execute(
            "SELECT run_record FROM runs WHERE run_id = %s",
            (run_id,),
        )
        row = await cursor.fetchone()

        if not row or not row[0]:
            return None

        record_data = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        return RunRecord.model_validate(record_data)

    @staticmethod
    async def check_idempotency(
        conn: AsyncConnection,
        idempotency_key: str,
        payload_hash: str,
    ) -> str | None:
        """Check if idempotency key exists.

        Args:
            conn: Async database connection
            idempotency_key: Idempotency key
            payload_hash: SHA256 hash of task_spec + candidate_output

        Returns:
            Existing run_id if found, None otherwise
        """
        cursor = await conn.execute(
            """
            SELECT run_id FROM runs
            WHERE idempotency_key = %s AND payload_hash = %s
            """,
            (idempotency_key, payload_hash),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    @staticmethod
    async def list_runs(
        conn: AsyncConnection,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[dict]:
        """List runs with pagination.

        Args:
            conn: Async database connection
            limit: Max results per page
            offset: Pagination offset
            status: Optional status filter (QUEUED, RUNNING, COMPLETED, FAILED)

        Returns:
            List of run dicts
        """
        query = "SELECT run_id, status, created_at, updated_at, task_spec, run_record FROM runs"
        params = []

        if status:
            query += " WHERE status = %s"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [
            {
                "run_id": row[0],
                "status": row[1],
                "created_at": row[2],
                "updated_at": row[3],
                "task_spec": row[4] if isinstance(row[4], dict) else json.loads(row[4]) if row[4] else None,
                "run_record": row[5] if isinstance(row[5], dict) else (json.loads(row[5]) if row[5] else None),
            }
            for row in rows
        ]

    @staticmethod
    async def count_runs(
        conn: AsyncConnection,
        status: str | None = None,
    ) -> int:
        """Count total runs (with optional status filter).

        Args:
            conn: Async database connection
            status: Optional status filter (QUEUED, RUNNING, COMPLETED, FAILED)

        Returns:
            Total count of runs
        """
        query = "SELECT COUNT(*) FROM runs"
        params = []

        if status:
            query += " WHERE status = %s"
            params.append(status)

        cursor = await conn.execute(query, params)
        row = await cursor.fetchone()
        return row[0] if row else 0

    # Sync methods for RQ worker

    @staticmethod
    def update_status_running(conn: Connection, run_id: str) -> None:
        """Update status to RUNNING (sync).

        Args:
            conn: Synchronous database connection
            run_id: Run identifier
        """
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE runs SET status = %s WHERE run_id = %s",
                ("RUNNING", run_id),
            )
        conn.commit()

    @staticmethod
    def update_completed(
        conn: Connection,
        run_id: str,
        run_record: dict,
    ) -> None:
        """Update status to COMPLETED and store run_record (sync).

        Args:
            conn: Synchronous database connection
            run_id: Run identifier
            run_record: Complete RunRecord dict
        """
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE runs
                SET status = %s, run_record = %s
                WHERE run_id = %s
                """,
                ("COMPLETED", json.dumps(run_record), run_id),
            )
        conn.commit()

    @staticmethod
    def update_failed(
        conn: Connection,
        run_id: str,
        error: str,
    ) -> None:
        """Update status to FAILED and store error (sync).

        Args:
            conn: Synchronous database connection
            run_id: Run identifier
            error: Error message
        """
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE runs
                SET status = %s, error = %s
                WHERE run_id = %s
                """,
                ("FAILED", error, run_id),
            )
        conn.commit()

    @staticmethod
    def get_run_sync(conn: Connection, run_id: str) -> dict | None:
        """Fetch run by ID (sync version for worker).

        Args:
            conn: Synchronous database connection
            run_id: Run identifier

        Returns:
            Dict with task_spec, candidate_output, or None if not found
        """
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT task_spec, candidate_output
                FROM runs WHERE run_id = %s
                """,
                (run_id,),
            )
            row = cur.fetchone()

        if not row:
            return None

        task_spec, candidate_output = row
        return {
            "task_spec": task_spec if isinstance(task_spec, dict) else json.loads(task_spec),
            "candidate_output": candidate_output if isinstance(candidate_output, dict) else json.loads(candidate_output),
        }
