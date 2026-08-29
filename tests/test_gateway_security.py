import pytest

import gateway.tool_registry

from gateway.gateway import (
    TOOL_REGISTRY,
    gateway_execute,
    register_tool,
)

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


def test_invalid_agent_identity_is_rejected():

    with pytest.raises(PermissionError):

        gateway_execute(
            "build_agent",
            Operation.DOCKER_BUILD,
            project_path="tests/docker-demo",
            image_name="unauthorized",
        )


def test_invalid_operation_identity_is_rejected():

    with pytest.raises(PermissionError):

        gateway_execute(
            AgentRole.BUILD,
            "cloud_run.deploy",
            project_id="secure-gcp-deployment-fleet",
            region="asia-south1",
            service_name="unauthorized-test",
            image_uri="invalid",
        )


def test_registered_operations_have_immutable_registry_entries():

    expected_operations = {
        Operation.DOCKERFILE_GENERATE,
        Operation.DOCKER_BUILD,
        Operation.DOCKER_INSPECT,
        Operation.CLOUD_BUILD,
        Operation.REGISTRY_VALIDATE,
        Operation.REGISTRY_TAG,
        Operation.REGISTRY_PUSH,
        Operation.REGISTRY_VERIFY,
        Operation.CLOUD_RUN_DEPLOY,
        Operation.CLOUD_RUN_GET,
    }

    assert set(TOOL_REGISTRY.keys()) == expected_operations

    for operation in expected_operations:
        assert callable(
            TOOL_REGISTRY[operation]
        )


def test_runtime_tool_registration_is_blocked():

    def malicious_tool(**kwargs):
        return "MALICIOUS"


    with pytest.raises(
        RuntimeError,
        match="registry is frozen",
    ):

        register_tool(
            Operation.CLOUD_RUN_DEPLOY,
            malicious_tool,
        )


def test_direct_tool_registry_mutation_is_blocked():

    with pytest.raises(
        TypeError,
    ):

        TOOL_REGISTRY[
            Operation.CLOUD_RUN_DEPLOY
        ] = lambda **kwargs: "MALICIOUS"
