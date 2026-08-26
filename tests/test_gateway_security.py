import pytest

import gateway.tool_registry

from gateway.gateway import gateway_execute
from gateway.policy import (
    AgentRole,
    Operation,
)


def test_build_agent_cannot_deploy_to_cloud_run():

    with pytest.raises(PermissionError):

        gateway_execute(
            AgentRole.BUILD,
            Operation.CLOUD_RUN_DEPLOY,
            project_id="secure-gcp-deployment-fleet",
            region="asia-south1",
            service_name="unauthorized-test",
            image_uri="invalid",
        )


def test_build_agent_cannot_read_cloud_run():

    with pytest.raises(PermissionError):

        gateway_execute(
            AgentRole.BUILD,
            Operation.CLOUD_RUN_GET,
            project_id="secure-gcp-deployment-fleet",
            region="asia-south1",
            service_name="secure-fleet-demo",
        )


def test_registry_agent_cannot_build():

    with pytest.raises(PermissionError):

        gateway_execute(
            AgentRole.REGISTRY,
            Operation.DOCKER_BUILD,
            project_path="tests/docker-demo",
            image_name="unauthorized",
        )


def test_registry_agent_cannot_deploy():

    with pytest.raises(PermissionError):

        gateway_execute(
            AgentRole.REGISTRY,
            Operation.CLOUD_RUN_DEPLOY,
            project_id="secure-gcp-deployment-fleet",
            region="asia-south1",
            service_name="unauthorized-test",
            image_uri="invalid",
        )


def test_hosting_agent_cannot_push():

    with pytest.raises(PermissionError):

        gateway_execute(
            AgentRole.HOSTING,
            Operation.REGISTRY_PUSH,
            project_id="secure-gcp-deployment-fleet",
            region="asia-south1",
            repository="secure-fleet",
            image_name="secure-fleet-streamlit",
            tag="v1",
        )


def test_hosting_agent_cannot_build():

    with pytest.raises(PermissionError):

        gateway_execute(
            AgentRole.HOSTING,
            Operation.DOCKER_BUILD,
            project_path="tests/docker-demo",
            image_name="unauthorized",
        )
