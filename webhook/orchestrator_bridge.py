from typing import Any

from webhook.github_webhook import (
    ReplayProtection,
    process_github_webhook,
)


def create_deployment_request(
    payload_bytes: bytes,
    signature: str | None,
    event_name: str,
    event_id: str,
    expected_repository: str,
    expected_branch: str = "main",
    replay_protection: ReplayProtection | None = None,
) -> dict[str, Any]:
    """
    Validate a GitHub webhook and convert it into an
    Orchestrator deployment request.

    No deployment tool is executed here.
    """

    event = process_github_webhook(
        payload_bytes=payload_bytes,
        signature=signature,
        event_name=event_name,
        event_id=event_id,
        expected_repository=expected_repository,
        expected_branch=expected_branch,
        replay_protection=replay_protection,
    )

    return {
        # Preserve the Phase 8C HTTP response contract.
        "accepted": True,

        # Phase 8D deployment request metadata.
        "request_type": "github_deployment",
        "source": "github",

        # Event information.
        "event_id": event["event_id"],
        "event": event["event"],
        "repository": event["repository"],
        "repository_owner": event["repository_owner"],
        "branch": event["branch"],
        "commit_sha": event["commit_sha"],
        "installation_id": event["installation_id"],
    }
