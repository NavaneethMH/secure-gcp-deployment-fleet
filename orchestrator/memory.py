from typing import Any

from memory.memory_bank import MemoryBank

memory_bank = MemoryBank()


def recall_project_history(
    project_id: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Recall recent deployment history for a project.
    """

    return memory_bank.get_project_history(
        project_id=project_id,
        limit=limit,
    )


def recall_service_history(
    project_id: str,
    service_name: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Recall recent deployment history for a Cloud Run service.
    """

    return memory_bank.get_service_history(
        project_id=project_id,
        service_name=service_name,
        limit=limit,
    )


def recall_last_success(
    project_id: str,
    service_name: str | None = None,
) -> dict[str, Any] | None:
    """
    Recall the latest successful deployment.
    """

    return memory_bank.get_latest_successful_deployment(
        project_id=project_id,
        service_name=service_name,
    )


def recall_last_failure(
    project_id: str,
    service_name: str | None = None,
) -> dict[str, Any] | None:
    """
    Recall the latest failed deployment.
    """

    return memory_bank.get_latest_failure(
        project_id=project_id,
        service_name=service_name,
    )


def remember_deployment(
    *,
    project_id: str,
    service_name: str,
    region: str,
    image_uri: str | None,
    image_digest: str | None,
    revision: str | None,
    service_url: str | None,
    status: str,
    error: str | None = None,
    constraints: str | None = None,
) -> str:
    """
    Persist the outcome of a deployment.
    """

    return memory_bank.record_deployment(
        project_id=project_id,
        service_name=service_name,
        region=region,
        image_uri=image_uri,
        image_digest=image_digest,
        revision=revision,
        service_url=service_url,
        status=status,
        error=error,
        constraints=constraints,
    )
