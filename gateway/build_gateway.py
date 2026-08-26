from typing import Any

from gateway.gateway import gateway_execute
from gateway.policy import (
    AgentRole,
    Operation,
)


def secure_docker_build(
    project_path: str,
    image_name: str,
) -> Any:

    return gateway_execute(
        AgentRole.BUILD,
        Operation.DOCKER_BUILD,
        project_path=project_path,
        image_name=image_name,
    )


def secure_docker_inspect(
    image_name: str,
) -> Any:

    return gateway_execute(
        AgentRole.BUILD,
        Operation.DOCKER_INSPECT,
        image_name=image_name,
    )
