import hashlib
import hmac
import json
import os
import time
from typing import Any, Optional

from webhook.models import GitHubPushEvent


SUPPORTED_EVENT = "push"
DEFAULT_BRANCH = "main"


class WebhookSecurityError(Exception):
    """Raised when a GitHub webhook fails security validation."""


class WebhookValidationError(Exception):
    """Raised when a GitHub webhook payload is invalid."""


def _get_webhook_secret() -> str:
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")

    if not secret:
        raise WebhookSecurityError(
            "GitHub webhook secret is not configured."
        )

    return secret


def verify_signature(
    payload: bytes,
    signature: Optional[str],
    secret: Optional[str] = None,
) -> bool:
    """Verify GitHub's X-Hub-Signature-256 header."""

    if not signature:
        return False

    if not signature.startswith("sha256="):
        return False

    secret = secret or _get_webhook_secret()

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def _validate_repository(repository: Any) -> tuple[str, str]:
    if not isinstance(repository, dict):
        raise WebhookValidationError(
            "Repository information is missing."
        )

    full_name = repository.get("full_name")
    owner = repository.get("owner", {}).get("login")

    if not isinstance(full_name, str) or not full_name:
        raise WebhookValidationError(
            "Invalid repository name."
        )

    if not isinstance(owner, str) or not owner:
        raise WebhookValidationError(
            "Invalid repository owner."
        )

    return full_name, owner


def parse_push_event(
    payload: dict[str, Any],
    event_id: str,
    expected_repository: Optional[str] = None,
    expected_branch: str = DEFAULT_BRANCH,
) -> GitHubPushEvent:
    """Validate and normalize a GitHub push event."""

    if not isinstance(payload, dict):
        raise WebhookValidationError(
            "Webhook payload must be a JSON object."
        )

    repository, owner = _validate_repository(
        payload.get("repository")
    )

    if expected_repository and repository != expected_repository:
        raise WebhookSecurityError(
            "Repository is not authorized."
        )

    ref = payload.get("ref")

    if not isinstance(ref, str):
        raise WebhookValidationError(
            "Git reference is missing."
        )

    expected_ref = f"refs/heads/{expected_branch}"

    if ref != expected_ref:
        raise WebhookValidationError(
            f"Unsupported branch. Expected {expected_ref}."
        )

    after = payload.get("after")

    if not isinstance(after, str) or len(after) != 40:
        raise WebhookValidationError(
            "Invalid commit SHA."
        )

    installation = payload.get("installation") or {}
    installation_id = installation.get("id")

    return GitHubPushEvent(
        event_id=event_id,
        repository=repository,
        repository_owner=owner,
        ref=ref,
        branch=expected_branch,
        commit_sha=after,
        installation_id=installation_id,
    )


class ReplayProtection:
    """Simple in-memory replay protection for webhook events."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._events: dict[str, float] = {}

    def seen(self, event_id: str) -> bool:
        now = time.time()

        expired = [
            key
            for key, timestamp in self._events.items()
            if now - timestamp > self.ttl_seconds
        ]

        for key in expired:
            del self._events[key]

        if event_id in self._events:
            return True

        self._events[event_id] = now
        return False


def process_github_webhook(
    payload_bytes: bytes,
    signature: Optional[str],
    event_name: str,
    event_id: str,
    expected_repository: Optional[str] = None,
    expected_branch: str = DEFAULT_BRANCH,
    replay_protection: Optional[ReplayProtection] = None,
) -> dict[str, Any]:
    """
    Validate a GitHub webhook and return a normalized deployment event.

    This function does not directly execute deployment operations.
    """

    if event_name != SUPPORTED_EVENT:
        raise WebhookValidationError(
            f"Unsupported GitHub event: {event_name}"
        )

    if not event_id:
        raise WebhookSecurityError(
            "Missing GitHub event ID."
        )

    if replay_protection and replay_protection.seen(event_id):
        raise WebhookSecurityError(
            "Duplicate or replayed GitHub event."
        )

    if not verify_signature(payload_bytes, signature):
        raise WebhookSecurityError(
            "Invalid GitHub webhook signature."
        )

    try:
        payload = json.loads(
            payload_bytes.decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WebhookValidationError(
            "Webhook payload is not valid JSON."
        ) from exc

    event = parse_push_event(
        payload=payload,
        event_id=event_id,
        expected_repository=expected_repository,
        expected_branch=expected_branch,
    )

    return {
        "accepted": True,
        "event_id": event.event_id,
        "event": "push",
        "repository": event.repository,
        "repository_owner": event.repository_owner,
        "branch": event.branch,
        "commit_sha": event.commit_sha,
        "installation_id": event.installation_id,
    }
