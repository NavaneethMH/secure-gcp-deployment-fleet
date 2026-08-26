from __future__ import annotations

import uuid
from typing import Any, Callable

from audit.audit_logger import (
    write_audit_event,
)

from gateway.policy import (
    AgentRole,
    Operation,
    authorize,
)


TOOL_REGISTRY: dict[
    Operation,
    Callable[..., Any],
] = {}


def register_tool(
    operation: Operation,
    tool: Callable[..., Any],
) -> None:

    TOOL_REGISTRY[operation] = tool


def _resource_from_kwargs(
    kwargs: dict[str, Any],
) -> str | None:

    for key in (
        "image_uri",
        "image_name",
        "service_name",
        "project_id",
        "project_path",
    ):

        value = kwargs.get(key)

        if value is not None:
            return str(value)

    return None


def gateway_execute(
    agent: AgentRole,
    operation: Operation,
    **kwargs: Any,
) -> Any:

    request_id = str(
        uuid.uuid4()
    )

    resource = _resource_from_kwargs(
        kwargs
    )

    decision = authorize(
        agent,
        operation,
    )

    if not decision.allowed:

        write_audit_event(
            agent=agent.value,
            operation=operation.value,
            decision="DENY",
            reason=decision.reason,
            status="BLOCKED",
            request_id=request_id,
            resource=resource,
        )

        raise PermissionError(
            f"Gateway denied operation "
            f"{operation.value}: "
            f"{decision.reason}"
        )

    tool = TOOL_REGISTRY.get(
        operation
    )

    if tool is None:

        reason = (
            f"No registered implementation exists "
            f"for {operation.value}"
        )

        write_audit_event(
            agent=agent.value,
            operation=operation.value,
            decision="DENY",
            reason=reason,
            status="BLOCKED",
            request_id=request_id,
            resource=resource,
        )

        raise PermissionError(
            reason
        )

    write_audit_event(
        agent=agent.value,
        operation=operation.value,
        decision="ALLOW",
        reason=decision.reason,
        status="AUTHORIZED",
        request_id=request_id,
        resource=resource,
    )

    try:

        result = tool(
            **kwargs
        )

        write_audit_event(
            agent=agent.value,
            operation=operation.value,
            decision="ALLOW",
            reason="Tool execution completed.",
            status="SUCCESS",
            request_id=request_id,
            resource=resource,
        )

        return result

    except Exception as exc:

        write_audit_event(
            agent=agent.value,
            operation=operation.value,
            decision="ALLOW",
            reason="Tool execution failed.",
            status="ERROR",
            request_id=request_id,
            resource=resource,
            error=(
                f"{type(exc).__name__}: "
                f"{exc}"
            ),
        )

        raise
