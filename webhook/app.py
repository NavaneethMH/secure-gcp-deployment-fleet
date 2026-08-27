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


app = FastAPI(
    title="Secure GCP Deployment Fleet Webhook",
    version="1.0.0",
)

replay_protection = ReplayProtection()


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "secure-gcp-deployment-fleet-webhook",
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
        result = create_deployment_request(
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

    return result
