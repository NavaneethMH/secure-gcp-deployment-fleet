import hashlib
import hmac
import json

import pytest

from webhook.github_webhook import (
    ReplayProtection,
    WebhookSecurityError,
    WebhookValidationError,
    process_github_webhook,
    verify_signature,
)


SECRET = "test-webhook-secret"
REPOSITORY = "NavaneethMH/secure-gcp-deployment-fleet"
COMMIT_SHA = "a" * 40


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


def test_valid_signature():
    payload = b'{"hello":"world"}'

    assert verify_signature(
        payload,
        make_signature(payload),
        SECRET,
    )


def test_invalid_signature():
    payload = b'{"hello":"world"}'

    assert not verify_signature(
        payload,
        "sha256=invalid",
        SECRET,
    )


def test_missing_signature():
    payload = b'{"hello":"world"}'

    assert not verify_signature(
        payload,
        None,
        SECRET,
    )


def test_valid_push_event(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(
        make_payload()
    ).encode()

    result = process_github_webhook(
        payload_bytes=payload,
        signature=make_signature(payload),
        event_name="push",
        event_id="event-001",
        expected_repository=REPOSITORY,
    )

    assert result["accepted"] is True
    assert result["repository"] == REPOSITORY
    assert result["branch"] == "main"
    assert result["commit_sha"] == COMMIT_SHA


def test_invalid_signature_is_blocked(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(
        make_payload()
    ).encode()

    with pytest.raises(WebhookSecurityError):
        process_github_webhook(
            payload,
            "sha256=invalid",
            "push",
            "event-002",
            expected_repository=REPOSITORY,
        )


def test_unsupported_event_is_blocked(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(
        make_payload()
    ).encode()

    with pytest.raises(WebhookValidationError):
        process_github_webhook(
            payload,
            make_signature(payload),
            "pull_request",
            "event-003",
            expected_repository=REPOSITORY,
        )


def test_wrong_repository_is_blocked(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(
        make_payload()
    ).encode()

    with pytest.raises(WebhookSecurityError):
        process_github_webhook(
            payload,
            make_signature(payload),
            "push",
            "event-004",
            expected_repository="attacker/repository",
        )


def test_wrong_branch_is_blocked(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    data = make_payload()
    data["ref"] = "refs/heads/dev"

    payload = json.dumps(data).encode()

    with pytest.raises(WebhookValidationError):
        process_github_webhook(
            payload,
            make_signature(payload),
            "push",
            "event-005",
            expected_repository=REPOSITORY,
        )


def test_invalid_commit_sha_is_blocked(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    data = make_payload()
    data["after"] = "invalid"

    payload = json.dumps(data).encode()

    with pytest.raises(WebhookValidationError):
        process_github_webhook(
            payload,
            make_signature(payload),
            "push",
            "event-006",
            expected_repository=REPOSITORY,
        )


def test_replay_is_blocked(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    protection = ReplayProtection()

    payload = json.dumps(
        make_payload()
    ).encode()

    process_github_webhook(
        payload,
        make_signature(payload),
        "push",
        "event-007",
        expected_repository=REPOSITORY,
        replay_protection=protection,
    )

    with pytest.raises(WebhookSecurityError):
        process_github_webhook(
            payload,
            make_signature(payload),
            "push",
            "event-007",
            expected_repository=REPOSITORY,
            replay_protection=protection,
        )


def test_malformed_json_is_blocked(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = b"not-json"

    with pytest.raises(WebhookValidationError):
        process_github_webhook(
            payload,
            make_signature(payload),
            "push",
            "event-008",
            expected_repository=REPOSITORY,
        )


def test_missing_event_id_is_blocked(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(
        make_payload()
    ).encode()

    with pytest.raises(WebhookSecurityError):
        process_github_webhook(
            payload,
            make_signature(payload),
            "push",
            "",
            expected_repository=REPOSITORY,
        )
