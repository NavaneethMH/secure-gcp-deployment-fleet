from typing import Any, Callable


class OrchestratorExecutionError(Exception):
    """Raised when a deployment request cannot be executed."""


def execute_deployment_request(
    deployment_request: dict[str, Any],
    orchestrator_handler: Callable[[dict[str, Any]], Any],
) -> Any:
    """
    Pass a validated deployment request to the Orchestrator.

    The webhook layer does not receive or execute deployment tools.
    The supplied orchestrator handler remains responsible for
    authorization and agent/tool execution.
    """

    if not isinstance(deployment_request, dict):
        raise OrchestratorExecutionError(
            "Deployment request must be a dictionary."
        )

    if deployment_request.get("accepted") is not True:
        raise OrchestratorExecutionError(
            "Deployment request was not accepted."
        )

    if deployment_request.get("request_type") != "github_deployment":
        raise OrchestratorExecutionError(
            "Unsupported deployment request type."
        )

    required_fields = (
        "event_id",
        "repository",
        "branch",
        "commit_sha",
    )

    missing = [
        field
        for field in required_fields
        if not deployment_request.get(field)
    ]

    if missing:
        raise OrchestratorExecutionError(
            f"Missing deployment request fields: {', '.join(missing)}"
        )

    return orchestrator_handler(deployment_request)
