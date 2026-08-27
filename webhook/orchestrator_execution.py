import inspect
from typing import Any, Awaitable, Callable


class OrchestratorExecutionError(Exception):
    """Raised when a deployment request cannot be executed."""


def _validate_request(
    deployment_request: dict[str, Any],
) -> None:
    if not isinstance(deployment_request, dict):
        raise OrchestratorExecutionError(
            "Deployment request must be a dictionary."
        )

    if deployment_request.get("accepted") is not True:
        raise OrchestratorExecutionError(
            "Deployment request was not accepted."
        )

    if deployment_request.get(
        "request_type"
    ) != "github_deployment":
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
            "Missing deployment request fields: "
            + ", ".join(missing)
        )


def execute_deployment_request(
    deployment_request: dict[str, Any],
    orchestrator_handler: Callable[
        [dict[str, Any]],
        Any,
    ],
) -> Any:
    """
    Synchronous Orchestrator execution adapter.

    Retained for existing callers and tests.
    """

    _validate_request(
        deployment_request
    )

    return orchestrator_handler(
        deployment_request
    )


async def execute_deployment_request_async(
    deployment_request: dict[str, Any],
    orchestrator_handler: Callable[
        [dict[str, Any]],
        Any,
    ],
) -> Any:
    """
    Async Orchestrator execution adapter.

    Supports both synchronous and asynchronous handlers.
    """

    _validate_request(
        deployment_request
    )

    result = orchestrator_handler(
        deployment_request
    )

    if inspect.isawaitable(result):
        return await result

    return result
