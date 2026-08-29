import httpx
import pytest

from webhook.orchestrator_client import (
    OrchestratorClient,
    OrchestratorClientError,
)

VALID_REQUEST = {
    "accepted": True,
    "request_type": "github_deployment",
    "source": "github",
    "event_id": "event-001",
    "repository": (
        "NavaneethMH/"
        "secure-gcp-deployment-fleet"
    ),
    "repository_owner": "NavaneethMH",
    "branch": "main",
    "commit_sha": "a" * 40,
    "installation_id": None,
}


def test_client_requires_orchestrator_url():
    client = OrchestratorClient(
        base_url=""
    )

    assert client.configured is False

    with pytest.raises(
        OrchestratorClientError
    ):
        import asyncio

        asyncio.run(
            client.execute(VALID_REQUEST)
        )


def test_prompt_contains_deployment_metadata():
    prompt = OrchestratorClient._build_prompt(
        VALID_REQUEST
    )

    assert "event-001" in prompt
    assert "NavaneethMH/" in prompt
    assert "secure-gcp-deployment-fleet" in prompt
    assert "main" in prompt
    assert "a" * 40 in prompt
    assert "Never bypass the Agent Gateway" in prompt


@pytest.mark.anyio
async def test_client_creates_session_and_runs_orchestrator(
    monkeypatch,
):
    requests = []

    class FakeResponse:
        def __init__(
            self,
            status_code,
            payload,
        ):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            tb,
        ):
            return False

        async def post(
            self,
            url,
            headers,
            json,
        ):
            requests.append(
                {
                    "url": url,
                    "headers": headers,
                    "json": json,
                }
            )

            if url.endswith("/sessions/event-001"):
                return FakeResponse(
                    201,
                    {"id": "deployment-event-001"},
                )

            return FakeResponse(
                200,
                [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "deployment complete"
                                }
                            ]
                        }
                    }
                ],
            )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        FakeAsyncClient,
    )

    client = OrchestratorClient(
        base_url="http://127.0.0.1:8000",
        app_name="orchestrator",
    )

    result = await client.execute(
        VALID_REQUEST
    )

    assert result["status"] == "completed"
    assert result["event_id"] == "event-001"
    assert result["app_name"] == "orchestrator"
    assert result["events_received"] == 1

    assert len(requests) == 2

    run_request = requests[1]

    assert run_request["url"] == (
        "http://127.0.0.1:8000/run"
    )

    assert (
        run_request["json"]["app_name"]
        == "orchestrator"
    )

    assert (
        run_request["json"]["user_id"]
        == "github-NavaneethMH"
    )

    assert (
        run_request["json"]["session_id"]
        == "deployment-event-001"
    )


@pytest.mark.anyio
async def test_client_rejects_failed_session_creation(
    monkeypatch,
):
    class FakeResponse:
        status_code = 500

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            tb,
        ):
            return False

        async def post(
            self,
            url,
            headers,
            json,
        ):
            return FakeResponse()

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        FakeAsyncClient,
    )

    client = OrchestratorClient(
        base_url="http://127.0.0.1:8000"
    )

    with pytest.raises(
        OrchestratorClientError,
        match="Failed to create Orchestrator session",
    ):
        await client.execute(
            VALID_REQUEST
        )


@pytest.mark.anyio
async def test_client_rejects_failed_orchestrator_execution(
    monkeypatch,
):
    call_count = 0

    class FakeResponse:
        def __init__(self, status_code):
            self.status_code = status_code

        def json(self):
            return []

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            tb,
        ):
            return False

        async def post(
            self,
            url,
            headers,
            json,
        ):
            nonlocal call_count

            call_count += 1

            if call_count == 1:
                return FakeResponse(201)

            return FakeResponse(500)

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        FakeAsyncClient,
    )

    client = OrchestratorClient(
        base_url="http://127.0.0.1:8000"
    )

    with pytest.raises(
        OrchestratorClientError,
        match="Orchestrator execution failed",
    ):
        await client.execute(
            VALID_REQUEST
        )
