from typing import Any

from gateway.gateway import gateway_execute
from gateway.policy import (
    AgentRole,
    Operation,
)


def secure_cloud_run_deploy(
    **kwargs: Any,
) -> Any:

    return gateway_execute(
        AgentRole.HOSTING,
        Operation.CLOUD_RUN_DEPLOY,
        **kwargs,
    )


def secure_cloud_run_get(
    project_id: str,
    region: str,
    service_name: str,
) -> Any:

    return gateway_execute(
        AgentRole.HOSTING,
        Operation.CLOUD_RUN_GET,
        project_id=project_id,
        region=region,
        service_name=service_name,
    )
