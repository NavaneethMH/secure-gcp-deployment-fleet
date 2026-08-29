from gateway.policy import (
    AgentRole,
    Operation,
    authorize,
)


def test_build_agent_can_remote_build():

    decision = authorize(
        AgentRole.BUILD,
        Operation.CLOUD_BUILD,
    )

    assert decision.allowed is True


def test_build_agent_can_build():

    decision = authorize(
        AgentRole.BUILD,
        Operation.DOCKER_BUILD,
    )

    assert decision.allowed is True


def test_build_agent_cannot_deploy():

    decision = authorize(
        AgentRole.BUILD,
        Operation.CLOUD_RUN_DEPLOY,
    )

    assert decision.allowed is False


def test_registry_agent_cannot_build():

    decision = authorize(
        AgentRole.REGISTRY,
        Operation.DOCKER_BUILD,
    )

    assert decision.allowed is False


def test_hosting_agent_can_deploy():

    decision = authorize(
        AgentRole.HOSTING,
        Operation.CLOUD_RUN_DEPLOY,
    )

    assert decision.allowed is True
