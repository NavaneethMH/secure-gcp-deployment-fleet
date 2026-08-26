from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MEMORY_DIRECTORY = Path("memory")
MEMORY_DATABASE = MEMORY_DIRECTORY / "memory.db"


def _utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


class MemoryBank:
    """
    Persistent deployment memory for the Secure GCP Deployment Fleet.

    The Memory Bank stores deployment metadata and outcomes.
    It must never be used to store plaintext credentials,
    API keys, access tokens, or secret values.
    """

    def __init__(
        self,
        database_path: Path | str = MEMORY_DATABASE,
    ) -> None:

        self.database_path = Path(
            database_path
        )

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    def _connect(
        self,
    ) -> sqlite3.Connection:

        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection

    def _initialize(self) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS deployments (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    service_name TEXT,
                    region TEXT,
                    image_uri TEXT,
                    image_digest TEXT,
                    revision TEXT,
                    service_url TEXT,
                    status TEXT NOT NULL,
                    error TEXT,
                    constraints TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_deployments_project
                ON deployments(project_id)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_deployments_service
                ON deployments(service_name)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_deployments_status
                ON deployments(status)
                """
            )

    def record_deployment(
        self,
        *,
        project_id: str,
        service_name: str | None = None,
        region: str | None = None,
        image_uri: str | None = None,
        image_digest: str | None = None,
        revision: str | None = None,
        service_url: str | None = None,
        status: str,
        error: str | None = None,
        constraints: str | None = None,
    ) -> str:

        record_id = str(
            uuid.uuid4()
        )

        with self._connect() as connection:

            connection.execute(
                """
                INSERT INTO deployments (
                    id,
                    project_id,
                    service_name,
                    region,
                    image_uri,
                    image_digest,
                    revision,
                    service_url,
                    status,
                    error,
                    constraints,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    project_id,
                    service_name,
                    region,
                    image_uri,
                    image_digest,
                    revision,
                    service_url,
                    status,
                    error,
                    constraints,
                    _utc_now(),
                ),
            )

        return record_id

    def get_project_history(
        self,
        project_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM deployments
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (
                    project_id,
                    limit,
                ),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def get_service_history(
        self,
        project_id: str,
        service_name: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM deployments
                WHERE project_id = ?
                  AND service_name = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (
                    project_id,
                    service_name,
                    limit,
                ),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def get_latest_successful_deployment(
        self,
        project_id: str,
        service_name: str | None = None,
    ) -> dict[str, Any] | None:

        with self._connect() as connection:

            if service_name:

                row = connection.execute(
                    """
                    SELECT *
                    FROM deployments
                    WHERE project_id = ?
                      AND service_name = ?
                      AND status = 'SUCCESS'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (
                        project_id,
                        service_name,
                    ),
                ).fetchone()

            else:

                row = connection.execute(
                    """
                    SELECT *
                    FROM deployments
                    WHERE project_id = ?
                      AND status = 'SUCCESS'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (project_id,),
                ).fetchone()

        if row is None:
            return None

        return dict(row)

    def get_latest_failure(
        self,
        project_id: str,
        service_name: str | None = None,
    ) -> dict[str, Any] | None:

        with self._connect() as connection:

            if service_name:

                row = connection.execute(
                    """
                    SELECT *
                    FROM deployments
                    WHERE project_id = ?
                      AND service_name = ?
                      AND status = 'FAILED'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (
                        project_id,
                        service_name,
                    ),
                ).fetchone()

            else:

                row = connection.execute(
                    """
                    SELECT *
                    FROM deployments
                    WHERE project_id = ?
                      AND status = 'FAILED'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (project_id,),
                ).fetchone()

        if row is None:
            return None

        return dict(row)
