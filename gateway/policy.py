from dataclasses import dataclass
from enum import Enum


class AgentRole(str, Enum):
    BUILD = "build_agent"
    REGISTRY = "registry_agent"
    HOSTING = "hosting_agent"


class Operation(str, Enum):
    DOCKERFILE_GENERATE = "dockerfile.generate"

    DOCKER_BUILD = "docker.build"
    DOCKER_INSPECT = "docker.inspect"
    CLOUD_BUILD = "cloud_build.submit"

    REGISTRY_VALIDATE = "registry.validate"
    REGISTRY_TAG = "registry.tag"
    REGISTRY_PUSH = "registry.push"
    REGISTRY_VERIFY = "registry.verify"

    CLOUD_RUN_DEPLOY = "cloud_run.deploy"
    CLOUD_RUN_GET = "cloud_run.get"


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


POLICY: dict[AgentRole, set[Operation]] = {
    AgentRole.BUILD: {
        Operation.DOCKERFILE_GENERATE,
        Operation.DOCKER_BUILD,
        Operation.DOCKER_INSPECT,
        Operation.CLOUD_BUILD,
    },

    AgentRole.REGISTRY: {
        Operation.REGISTRY_VALIDATE,
        Operation.REGISTRY_TAG,
        Operation.REGISTRY_PUSH,
        Operation.REGISTRY_VERIFY,
    },

    AgentRole.HOSTING: {
        Operation.CLOUD_RUN_DEPLOY,
        Operation.CLOUD_RUN_GET,
    },
}


def authorize(
    agent: AgentRole,
    operation: Operation,
) -> PolicyDecision:

    allowed_operations = POLICY.get(agent, set())

    if operation in allowed_operations:
        return PolicyDecision(
            allowed=True,
            reason=(
                f"{agent.value} is authorized for "
                f"{operation.value}"
            ),
        )

    return PolicyDecision(
        allowed=False,
        reason=(
            f"{agent.value} is NOT authorized for "
            f"{operation.value}"
        ),
    )
