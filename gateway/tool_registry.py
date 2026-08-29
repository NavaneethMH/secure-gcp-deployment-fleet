from gateway.gateway import (
    freeze_tool_registry,
    register_tool,
)
from gateway.policy import Operation
from tools.artifact_registry_tools import (
    push_image_to_artifact_registry,
    tag_image_for_artifact_registry,
    validate_local_image,
)
from tools.cloud_build_tools import submit_cloud_build, verify_published_image
from tools.cloud_run_tools import (
    deploy_cloud_run_service,
    get_cloud_run_service,
)

# ---------------------------------------------------------------------------
# BUILD AGENT
# ---------------------------------------------------------------------------

register_tool(
    Operation.CLOUD_BUILD,
    submit_cloud_build,
)


# ---------------------------------------------------------------------------
# REGISTRY AGENT
# ---------------------------------------------------------------------------

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
    verify_published_image,
)


# ---------------------------------------------------------------------------
# HOSTING AGENT
# ---------------------------------------------------------------------------

register_tool(
    Operation.CLOUD_RUN_DEPLOY,
    deploy_cloud_run_service,
)

register_tool(
    Operation.CLOUD_RUN_GET,
    get_cloud_run_service,
)


# ---------------------------------------------------------------------------
# SECURITY BOUNDARY
# ---------------------------------------------------------------------------
#
# All approved tools are registered exactly once.
# Runtime tool registration/replacement is not permitted.
#

freeze_tool_registry()
