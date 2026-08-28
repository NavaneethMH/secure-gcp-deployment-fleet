from typing import Any
import gateway.tool_registry  # noqa: F401

from gateway.gateway import gateway_execute
from gateway.policy import (
    AgentRole,
    Operation,
)


def secure_generate_dockerfile(
    project_path: str,
    framework: str,
    runtime: str,
    startup_command: str,
    port: int,
) -> Any:

    return gateway_execute(
        AgentRole.BUILD,
        Operation.DOCKERFILE_GENERATE,
        project_path=project_path,
        framework=framework,
        runtime=runtime,
        startup_command=startup_command,
        port=port,
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
