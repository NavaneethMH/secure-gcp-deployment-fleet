import asyncio
import logging
import os

from fastapi import FastAPI, Header, HTTPException, Request

from webhook.github_webhook import (
    ReplayProtection,
    WebhookSecurityError,
    WebhookValidationError,
)

from webhook.orchestrator_bridge import (
    create_deployment_request,
)

from webhook.orchestrator_execution import (
    OrchestratorExecutionError,
    execute_deployment_request_async,
)

from webhook.orchestrator_client import (
    OrchestratorClient,
    OrchestratorClientError,
)


logger = logging.getLogger(__name__)


app = FastAPI(
    title="Secure GCP Deployment Fleet Webhook",
    version="1.2.0",
)


replay_protection = ReplayProtection()


async def _run_deployment(
    deployment_request: dict,
) -> None:
    """
    Execute the validated deployment request asynchronously.

    The webhook response is returned immediately after validation.
    """

    try:
        client = OrchestratorClient()

        result = await execute_deployment_request_async(
            deployment_request,
            client.execute,
        )

        logger.info(
            "Asynchronous deployment completed: "
            "event_id=%s status=%s session_id=%s",
            deployment_request.get("event_id"),
            result.get("status")
            if isinstance(result, dict)
            else None,
            result.get("session_id")
            if isinstance(result, dict)
            else None,
        )

    except (
        OrchestratorExecutionError,
        OrchestratorClientError,
    ):
        logger.exception(
            "Asynchronous deployment execution failed: "
            "event_id=%s",
            deployment_request.get("event_id"),
        )

    except Exception:
        logger.exception(
            "Unexpected asynchronous deployment failure: "
            "event_id=%s",
            deployment_request.get("event_id"),
        )


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "secure-gcp-deployment-fleet-webhook",
        "orchestrator_configured": bool(
            os.getenv("ORCHESTRATOR_URL")
        ),
    }


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
):
    payload = await request.body()

    if not x_github_event:
        raise HTTPException(
            status_code=400,
            detail="Missing X-GitHub-Event header.",
        )

    if not x_github_delivery:
        raise HTTPException(
            status_code=400,
            detail="Missing X-GitHub-Delivery header.",
        )

    try:
        deployment_request = create_deployment_request(
            payload_bytes=payload,
            signature=x_hub_signature_256,
            event_name=x_github_event,
            event_id=x_github_delivery,
            expected_repository=os.getenv(
                "GITHUB_REPOSITORY",
                "NavaneethMH/secure-gcp-deployment-fleet",
            ),
            expected_branch=os.getenv(
                "GITHUB_BRANCH",
                "main",
            ),
            replay_protection=replay_protection,
        )

    except WebhookSecurityError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except WebhookValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    # ---------------------------------------------------------------
    # The webhook has now passed:
    #   1. Header validation
    #   2. Signature validation
    #   3. Replay protection
    #   4. Deployment request validation
    #
    # Do not wait for the Orchestrator here.
    # ---------------------------------------------------------------

    if os.getenv("ORCHESTRATOR_URL"):
        asyncio.create_task(
            _run_deployment(
                deployment_request
            )
        )

    # Preserve the existing webhook API contract.
    #
    # The asynchronous execution change must not unnecessarily alter
    # the existing successful response expected by the application/tests.
    return deployment_request
