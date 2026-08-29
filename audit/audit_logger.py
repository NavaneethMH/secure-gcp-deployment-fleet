from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_DIRECTORY = Path("audit")
AUDIT_FILE = AUDIT_DIRECTORY / "logs.jsonl"

_lock = threading.Lock()


def write_audit_event(
    *,
    agent: str,
    operation: str,
    decision: str,
    reason: str,
    status: str,
    request_id: str,
    resource: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:

    event = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "request_id": request_id,

        "component": "agent_gateway",

        "agent": agent,

        "operation": operation,

        "decision": decision,

        "status": status,

        "reason": reason,

        "resource": resource,

        "error": error,
    }

    AUDIT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialized = json.dumps(
        event,
        separators=(",", ":"),
    )

    with _lock, AUDIT_FILE.open(
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            serialized + "\n"
        )

    return event
