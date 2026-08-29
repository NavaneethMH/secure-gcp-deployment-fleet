from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

from audit.audit_logger import write_audit_event
from gateway.policy import (
    AgentRole,
    Operation,
    authorize,
)

_TOOL_REGISTRY: dict[
    Operation,
    Callable[..., Any],
] = {}

TOOL_REGISTRY: Mapping[
    Operation,
    Callable[..., Any],
] = MappingProxyType(
    _TOOL_REGISTRY
)

_TOOL_REGISTRY_FROZEN = False


def register_tool(
    operation: Operation,
    tool: Callable[..., Any],
) -> None:
    """
    Register one approved implementation during gateway bootstrap only.

    Tool registration is intentionally one-way:
    - operation must be a valid Operation enum
    - implementation must be callable
    - an existing operation cannot be replaced
    - registration is rejected after the registry is frozen
    """

    if _TOOL_REGISTRY_FROZEN:
        raise RuntimeError(
            "Tool registry is frozen; runtime tool registration is not allowed."
        )

    if not isinstance(operation, Operation):
        raise TypeError(
            "operation must be an Operation enum value."
        )

    if not callable(tool):
        raise TypeError(
            "tool must be callable."
        )

    if operation in _TOOL_REGISTRY:
        raise RuntimeError(
            f"Tool already registered for operation: "
            f"{operation.value}"
        )

    _TOOL_REGISTRY[operation] = tool


def freeze_tool_registry() -> None:
    """
    Freeze the gateway registry after bootstrap registration.

    After this point:
    - register_tool() cannot add or replace tools
    - TOOL_REGISTRY cannot be mutated directly
    """

    global TOOL_REGISTRY
    global _TOOL_REGISTRY_FROZEN

    if _TOOL_REGISTRY_FROZEN:
        return

    TOOL_REGISTRY = MappingProxyType(
        dict(_TOOL_REGISTRY)
    )

    _TOOL_REGISTRY_FROZEN = True


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

    # ---------------------------------------------------------------
    # Strict agent identity validation
    # ---------------------------------------------------------------

    if not isinstance(agent, AgentRole):

        reason = "Invalid agent identity."

        write_audit_event(
            agent=str(agent),
            operation=(
                operation.value
                if isinstance(operation, Operation)
                else str(operation)
            ),
            decision="DENY",
            reason=reason,
            status="BLOCKED",
            request_id=request_id,
            resource=resource,
        )

        raise PermissionError(
            reason
        )

    # ---------------------------------------------------------------
    # Strict operation identity validation
    # ---------------------------------------------------------------

    if not isinstance(operation, Operation):

        reason = "Invalid operation identity."

        write_audit_event(
            agent=agent.value,
            operation=str(operation),
            decision="DENY",
            reason=reason,
            status="BLOCKED",
            request_id=request_id,
            resource=resource,
        )

        raise PermissionError(
            reason
        )

    # ---------------------------------------------------------------
    # Policy authorization
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Approved tool lookup
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Authorized execution
    # ---------------------------------------------------------------

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
