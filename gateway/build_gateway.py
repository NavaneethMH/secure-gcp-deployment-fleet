from typing import Any

import gateway.tool_registry  # noqa: F401
from gateway.gateway import gateway_execute
from gateway.policy import (
    AgentRole,
    Operation,
)


def secure_cloud_build(
    repository_url: str,
    commit_sha: str,
    project_id: str,
    region: str,
    artifact_repository: str,
    image_name: str,
    dockerfile: str = "Dockerfile",
    image_tag: str = "",
) -> Any:
    """Submit a source-controlled container build to Cloud Build."""

    return gateway_execute(
        AgentRole.BUILD,
        Operation.CLOUD_BUILD,
        repository_url=repository_url,
        commit_sha=commit_sha,
        project_id=project_id,
        region=region,
        artifact_repository=artifact_repository,
        image_name=image_name,
        dockerfile=dockerfile,
        image_tag=image_tag,
    )
