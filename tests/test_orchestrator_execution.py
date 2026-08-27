import pytest

from webhook.orchestrator_execution import (
    OrchestratorExecutionError,
    execute_deployment_request,
)


def valid_request():
    return {
        "accepted": True,
        "request_type": "github_deployment",
        "source": "github",
        "event_id": "event-001",
        "repository": "NavaneethMH/secure-gcp-deployment-fleet",
        "repository_owner": "NavaneethMH",
        "branch": "main",
        "commit_sha": "a" * 40,
        "installation_id": None,
    }


def test_valid_request_reaches_orchestrator():
    received = []

    def fake_orchestrator(request):
        received.append(request)
        return {
            "status": "accepted",
        }

    result = execute_deployment_request(
        valid_request(),
        fake_orchestrator,
    )

    assert result["status"] == "accepted"
    assert len(received) == 1
    assert received[0]["event_id"] == "event-001"


def test_rejected_request_does_not_reach_orchestrator():
    called = False

    def fake_orchestrator(request):
        nonlocal called
        called = True
        return {}

    request = valid_request()
    request["accepted"] = False

    with pytest.raises(OrchestratorExecutionError):
        execute_deployment_request(
            request,
            fake_orchestrator,
        )

    assert called is False


def test_invalid_request_type_is_blocked():
    request = valid_request()
    request["request_type"] = "arbitrary_execution"

    with pytest.raises(OrchestratorExecutionError):
        execute_deployment_request(
            request,
            lambda request: {},
        )


def test_missing_required_field_is_blocked():
    request = valid_request()
    del request["commit_sha"]

    with pytest.raises(OrchestratorExecutionError):
        execute_deployment_request(
            request,
            lambda request: {},
        )


def test_non_dictionary_request_is_blocked():
    with pytest.raises(OrchestratorExecutionError):
        execute_deployment_request(
            "invalid",
            lambda request: {},
        )


def test_orchestrator_result_is_returned():
    expected = {
        "status": "deployment_started",
        "request_id": "req-001",
    }

    result = execute_deployment_request(
        valid_request(),
        lambda request: expected,
    )

    assert result == expected


def test_execution_does_not_directly_execute_tools():
    """
    The execution bridge accepts only an Orchestrator handler.
    Deployment tools are not exposed by this module.
    """

    request = valid_request()

    result = execute_deployment_request(
        request,
        lambda deployment_request: "orchestrator-handled",
    )

    assert result == "orchestrator-handled"
