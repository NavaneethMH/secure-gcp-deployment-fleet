from gateway.gateway import register_tool
from gateway.policy import Operation

from tools.docker_tools import (
    docker_build,
    docker_inspect,
)

from tools.artifact_registry_tools import (
    validate_local_image,
    tag_image_for_artifact_registry,
    push_image_to_artifact_registry,
    verify_artifact_digest,
)

from tools.cloud_run_tools import (
    deploy_cloud_run_service,
    get_cloud_run_service,
)


register_tool(
    Operation.DOCKER_BUILD,
    docker_build,
)

register_tool(
    Operation.DOCKER_INSPECT,
    docker_inspect,
)

register_tool(
    Operation.REGISTRY_VALIDATE,
    validate_local_image,
)

register_tool(
    Operation.REGISTRY_TAG,
    tag_image_for_artifact_registry,
)

register_tool(
    Operation.REGISTRY_PUSH,
    push_image_to_artifact_registry,
)

register_tool(
    Operation.REGISTRY_VERIFY,
    verify_artifact_digest,
)

register_tool(
    Operation.CLOUD_RUN_DEPLOY,
    deploy_cloud_run_service,
)

register_tool(
    Operation.CLOUD_RUN_GET,
    get_cloud_run_service,
)
