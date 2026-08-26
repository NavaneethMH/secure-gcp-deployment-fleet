import json

from audit.audit_logger import (
    AUDIT_FILE,
    write_audit_event,
)


def test_audit_event_is_persisted(
    tmp_path,
    monkeypatch,
):

    audit_directory = tmp_path / "audit"
    audit_file = (
        audit_directory / "logs.jsonl"
    )

    import audit.audit_logger as logger

    monkeypatch.setattr(
        logger,
        "AUDIT_DIRECTORY",
        audit_directory,
    )

    monkeypatch.setattr(
        logger,
        "AUDIT_FILE",
        audit_file,
    )

    event = write_audit_event(
        agent="build_agent",
        operation="docker.build",
        decision="ALLOW",
        reason="Authorized operation.",
        status="SUCCESS",
        request_id="test-request-001",
        resource="tests/docker-demo",
    )

    assert audit_file.exists()

    lines = audit_file.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    stored = json.loads(
        lines[0]
    )

    assert stored["request_id"] == (
        "test-request-001"
    )

    assert stored["agent"] == (
        "build_agent"
    )

    assert stored["operation"] == (
        "docker.build"
    )

    assert stored["decision"] == (
        "ALLOW"
    )

    assert stored["status"] == (
        "SUCCESS"
    )


def test_audit_contains_security_fields(
    tmp_path,
    monkeypatch,
):

    audit_directory = tmp_path / "audit"
    audit_file = (
        audit_directory / "logs.jsonl"
    )

    import audit.audit_logger as logger

    monkeypatch.setattr(
        logger,
        "AUDIT_DIRECTORY",
        audit_directory,
    )

    monkeypatch.setattr(
        logger,
        "AUDIT_FILE",
        audit_file,
    )

    write_audit_event(
        agent="build_agent",
        operation="cloud_run.deploy",
        decision="DENY",
        reason="Unauthorized operation.",
        status="BLOCKED",
        request_id="test-request-002",
    )

    stored = json.loads(
        audit_file.read_text(
            encoding="utf-8"
        ).splitlines()[0]
    )

    required_fields = {
        "timestamp",
        "request_id",
        "component",
        "agent",
        "operation",
        "decision",
        "status",
        "reason",
        "resource",
        "error",
    }

    assert required_fields.issubset(
        stored.keys()
    )
