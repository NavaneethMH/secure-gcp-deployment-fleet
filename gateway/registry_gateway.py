from typing import Any

import gateway.tool_registry  # noqa: F401
from gateway.gateway import gateway_execute
from gateway.policy import (
    AgentRole,
    Operation,
)


def secure_validate_local_image(image_name: str) -> Any:
    return gateway_execute(
        AgentRole.REGISTRY,
        Operation.REGISTRY_VALIDATE,
        image_name=image_name,
    )


def secure_tag_image(
    local_image: str,
    project_id: str,
    region: str,
    repository: str,
    image_name: str,
    tag: str,
) -> Any:
    return gateway_execute(
        AgentRole.REGISTRY,
        Operation.REGISTRY_TAG,
        local_image=local_image,
        project_id=project_id,
        region=region,
        repository=repository,
        image_name=image_name,
        tag=tag,
    )


def secure_push_image(
    project_id: str,
    region: str,
    repository: str,
    image_name: str,
    tag: str,
) -> Any:
    return gateway_execute(
        AgentRole.REGISTRY,
        Operation.REGISTRY_PUSH,
        project_id=project_id,
        region=region,
        repository=repository,
        image_name=image_name,
        tag=tag,
    )


def secure_verify_digest(
    project_id: str,
    region: str,
    repository: str,
    image_name: str,
    tag: str,
) -> Any:
    return gateway_execute(
        AgentRole.REGISTRY,
        Operation.REGISTRY_VERIFY,
        project_id=project_id,
        region=region,
        artifact_repository=repository,
        image_name=image_name,
        image_tag=tag,
    )
