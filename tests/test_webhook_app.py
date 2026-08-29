import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from webhook.app import app

SECRET = "test-webhook-secret"
REPOSITORY = "NavaneethMH/secure-gcp-deployment-fleet"
COMMIT_SHA = "a" * 40

client = TestClient(app)


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


def headers(payload: bytes, delivery_id: str = "delivery-001"):
    return {
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": delivery_id,
        "X-Hub-Signature-256": make_signature(payload),
    }


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_github_webhook_accepts_valid_event(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(make_payload()).encode()

    response = client.post(
        "/webhooks/github",
        content=payload,
        headers=headers(payload),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["accepted"] is True
    assert body["event"] == "push"
    assert body["repository"] == REPOSITORY
    assert body["branch"] == "main"
    assert body["commit_sha"] == COMMIT_SHA


def test_missing_signature_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(make_payload()).encode()

    request_headers = {
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": "delivery-002",
    }

    response = client.post(
        "/webhooks/github",
        content=payload,
        headers=request_headers,
    )

    assert response.status_code == 403


def test_invalid_signature_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(make_payload()).encode()

    request_headers = {
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": "delivery-003",
        "X-Hub-Signature-256": "sha256=invalid",
    }

    response = client.post(
        "/webhooks/github",
        content=payload,
        headers=request_headers,
    )

    assert response.status_code == 403


def test_missing_event_header_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(make_payload()).encode()

    request_headers = {
        "X-GitHub-Delivery": "delivery-004",
        "X-Hub-Signature-256": make_signature(payload),
    }

    response = client.post(
        "/webhooks/github",
        content=payload,
        headers=request_headers,
    )

    assert response.status_code == 400


def test_missing_delivery_header_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(make_payload()).encode()

    request_headers = {
        "X-GitHub-Event": "push",
        "X-Hub-Signature-256": make_signature(payload),
    }

    response = client.post(
        "/webhooks/github",
        content=payload,
        headers=request_headers,
    )

    assert response.status_code == 400


def test_unsupported_event_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(make_payload()).encode()

    request_headers = {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": "delivery-005",
        "X-Hub-Signature-256": make_signature(payload),
    }

    response = client.post(
        "/webhooks/github",
        content=payload,
        headers=request_headers,
    )

    assert response.status_code == 400


def test_replayed_delivery_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        SECRET,
    )

    payload = json.dumps(make_payload()).encode()

    request_headers = headers(
        payload,
        delivery_id="delivery-replay",
    )

    first = client.post(
        "/webhooks/github",
        content=payload,
        headers=request_headers,
    )

    second = client.post(
        "/webhooks/github",
        content=payload,
        headers=request_headers,
    )

    assert first.status_code == 200
    assert second.status_code == 403
