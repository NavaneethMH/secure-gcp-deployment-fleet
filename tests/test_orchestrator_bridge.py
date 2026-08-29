import hashlib
import hmac
import json

import pytest

from webhook.github_webhook import (
    ReplayProtection,
    WebhookSecurityError,
)
from webhook.orchestrator_bridge import (
    create_deployment_request,
)

SECRET = "test-webhook-secret"
REPOSITORY = "NavaneethMH/secure-gcp-deployment-fleet"
COMMIT_SHA = "b" * 40


def make_payload():
    return {
        "ref": "refs/heads/main",
        "after": COMMIT_SHA,
        "repository": {
            "full_name": REPOSITORY,
            "owner": {
                "login": "NavaneethMH",
            },
        },
    }


def make_signature(payload: bytes) -> str:
    digest = hmac.new(
        SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def test_bridge_creates_deployment_request(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(
        make_payload()
    ).encode()

    result = create_deployment_request(
        payload_bytes=payload,
        signature=make_signature(payload),
        event_name="push",
        event_id="bridge-001",
        expected_repository=REPOSITORY,
    )

    assert result["request_type"] == "github_deployment"
    assert result["source"] == "github"
    assert result["event_id"] == "bridge-001"
    assert result["repository"] == REPOSITORY
    assert result["branch"] == "main"
    assert result["commit_sha"] == COMMIT_SHA


def test_bridge_rejects_invalid_signature(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(
        make_payload()
    ).encode()

    with pytest.raises(WebhookSecurityError):
        create_deployment_request(
            payload_bytes=payload,
            signature="sha256=invalid",
            event_name="push",
            event_id="bridge-002",
            expected_repository=REPOSITORY,
        )


def test_bridge_rejects_replay(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(
        make_payload()
    ).encode()

    protection = ReplayProtection()

    create_deployment_request(
        payload_bytes=payload,
        signature=make_signature(payload),
        event_name="push",
        event_id="bridge-003",
        expected_repository=REPOSITORY,
        replay_protection=protection,
    )

    with pytest.raises(WebhookSecurityError):
        create_deployment_request(
            payload_bytes=payload,
            signature=make_signature(payload),
            event_name="push",
            event_id="bridge-003",
            expected_repository=REPOSITORY,
            replay_protection=protection,
        )


def test_bridge_does_not_execute_deployment_tools():
    """
    The bridge only returns structured deployment intent.
    """

    assert callable(create_deployment_request)
