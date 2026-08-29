# Secure GCP Deployment Fleet

Secure agentic deployment orchestration for Google Cloud.

## Deployment path

Browser -> Streamlit -> ADK Orchestrator -> Build Agent -> Agent Gateway -> Cloud Build -> Artifact Registry -> Registry Agent -> Hosting Agent -> Cloud Run

The Build Agent does not depend on a local Docker daemon. It submits the exact GitHub commit to Google Cloud Build, which performs the Docker build and publishes the image to Artifact Registry. The Registry Agent verifies the published artifact and returns an immutable digest. The Hosting Agent deploys only that immutable digest to Cloud Run.

## Required GCP services

- Cloud Build API
- Artifact Registry API
- Cloud Run API
- Vertex AI / Gemini access used by ADK

## Source requirement

The deployment commit must contain the application source and the root `Dockerfile` used by the Build Agent.
