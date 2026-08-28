from typing import Any

from gateway.gateway import gateway_execute
from gateway.policy import (
    AgentRole,
    Operation,
)


def secure_cloud_run_deploy(
    project_id: str,
    region: str,
    service_name: str,
    image_uri: str,
    port: int = 8080,
    cpu: str = "1",
    memory: str = "512Mi",
    min_instances: int = 0,
    max_instances: int = 10,
    public: bool = True,
) -> Any:
    """
    Secure gateway wrapper for Cloud Run deployment.

    The explicit function signature is intentional:
    Google ADK uses this signature to generate the tool schema
    presented to the model.

    All actual infrastructure execution remains behind
    gateway_execute() and the immutable tool registry.
    """

    return gateway_execute(
        AgentRole.HOSTING,
        Operation.CLOUD_RUN_DEPLOY,
        project_id=project_id,
        region=region,
        service_name=service_name,
        image_uri=image_uri,
        port=port,
        cpu=cpu,
        memory=memory,
        min_instances=min_instances,
        max_instances=max_instances,
        public=public,
    )


def secure_cloud_run_get(
    project_id: str,
    region: str,
    service_name: str,
) -> Any:
    """
    Secure gateway wrapper for Cloud Run service verification.
    """

    return gateway_execute(
        AgentRole.HOSTING,
        Operation.CLOUD_RUN_GET,
        project_id=project_id,
        region=region,
        service_name=service_name,
    )
