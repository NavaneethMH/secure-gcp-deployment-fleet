import os
import uuid
import json
import requests
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2 import id_token


# ============================================================
# Configuration
# ============================================================

ORCHESTRATOR_URL = os.getenv(
    "ORCHESTRATOR_URL",
    "https://orchestrator-uhbaednxsq-el.a.run.app",
).rstrip("/")

APP_NAME = os.getenv(
    "ORCHESTRATOR_APP_NAME",
    "orchestrator",
)

GCP_PROJECT = os.getenv(
    "GOOGLE_CLOUD_PROJECT",
    "secure-gcp-deployment-fleet",
)

ARTIFACT_REGISTRY_REPOSITORY = os.getenv(
    "ARTIFACT_REGISTRY_REPOSITORY",
    "secure-fleet",
)


# ============================================================
# Page
# ============================================================

st.set_page_config(
    page_title="Secure GCP Deployment Fleet",
    page_icon="",
    layout="wide",
)

st.title("Secure GCP Deployment Fleet")
st.caption(
    "Secure agentic deployment orchestration for Google Cloud."
)

st.divider()


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.header("Fleet Status")

    st.success("Streamlit UI: Online")
    st.info("Orchestrator: Configured")
    st.info("Build Agent: Ready")
    st.info("Registry Agent: Ready")
    st.info("Hosting Agent: Ready")

    st.divider()

    st.caption("Orchestrator endpoint")
    st.code(ORCHESTRATOR_URL, language="text")


# ============================================================
# Deployment configuration
# ============================================================

st.subheader("Deploy an Application")

col1, col2 = st.columns(2)

with col1:
    repository_owner = st.text_input(
        "GitHub Owner",
        value="NavaneethMH",
    )

    repository = st.text_input(
        "Repository",
        value="secure-gcp-deployment-fleet",
    )

    branch = st.text_input(
        "Branch",
        value="main",
    )

with col2:
    commit_sha = st.text_input(
        "Commit SHA",
        value="",
        help="Enter the Git commit SHA to deploy.",
    )

    service_name = st.text_input(
        "Cloud Run Service",
        value="secure-fleet-demo",
    )

    region = st.text_input(
        "GCP Region",
        value="asia-south1",
    )

    project_id = st.text_input(
        "GCP Project",
        value=GCP_PROJECT,
    )


st.divider()


# ============================================================
# Authentication
# ============================================================

def get_identity_token() -> str:
    credentials = id_token.fetch_id_token_credentials(
        ORCHESTRATOR_URL,
        request=Request(),
    )

    credentials.refresh(Request())

    if not credentials.token:
        raise RuntimeError(
            "Unable to obtain Google identity token."
        )

    return credentials.token


# ============================================================
# Orchestrator execution
# ============================================================

def execute_deployment() -> dict:

    event_id = str(uuid.uuid4())

    user_id = (
        "streamlit-"
        + repository_owner
    )

    session_id = (
        "deployment-"
        + event_id
    )

    token = get_identity_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    session_url = (
        f"{ORCHESTRATOR_URL}"
        f"/apps/{APP_NAME}"
        f"/users/{user_id}"
        f"/sessions/{session_id}"
    )

    response = requests.post(
        session_url,
        headers=headers,
        json={},
        timeout=60,
    )

    response.raise_for_status()

    prompt = f"""
Execute a secure GCP deployment.

Repository:
{repository_owner}/{repository}

Repository URL:
https://github.com/{repository_owner}/{repository}.git

Branch:
{branch}

Commit SHA:
{commit_sha}

Target Cloud Run service:
{service_name}

GCP project:
{project_id}

GCP region:
{region}

Artifact Registry repository:
{ARTIFACT_REGISTRY_REPOSITORY}

Container image name:
{service_name}

Dockerfile:
Dockerfile

Follow the complete Secure GCP Deployment Fleet workflow.

Use the Build Agent for the remote Cloud Build container build.

Use the Registry Agent to verify the published Artifact Registry image and return its immutable digest.

Use the Hosting Agent for Cloud Run deployment.

Enforce the Agent Gateway and separation-of-duties controls.

Verify the resulting Cloud Run deployment.

Persist successful deployment metadata in the Memory Bank.

Return a concise deployment report containing:
- build result
- image URI
- image digest
- Artifact Registry result
- Cloud Run revision
- Cloud Run URL
- verification result
- overall status
"""

    run_url = f"{ORCHESTRATOR_URL}/run"

    run_payload = {
        "app_name": APP_NAME,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [
                {
                    "text": prompt,
                }
            ],
        },
    }

    response = requests.post(
        run_url,
        headers=headers,
        json=run_payload,
        timeout=300,
    )

    response.raise_for_status()

    return {
        "event_id": event_id,
        "session_id": session_id,
        "events": response.json(),
    }


# ============================================================
# UI action
# ============================================================

if st.button(
    "Deploy with Secure GCP Deployment Fleet",
    type="primary",
    use_container_width=True,
):

    if not repository_owner:
        st.error("GitHub owner is required.")

    elif not repository:
        st.error("Repository is required.")

    elif not branch:
        st.error("Branch is required.")

    elif not commit_sha:
        st.error("Commit SHA is required.")

    elif not project_id:
        st.error("GCP project is required.")

    else:

        with st.spinner(
            "Orchestrator is coordinating the deployment agents..."
        ):

            try:

                result = execute_deployment()

                st.subheader("Deployment Execution")
                st.json(result)

                events = result.get("events", [])
                serialized = json.dumps(events).upper()

                if "OVERALL STATUS: SUCCESS" in serialized or "STATUS=SUCCESS" in serialized:
                    st.success("Deployment completed successfully.")
                elif "ERROR:" in serialized or "FAILED" in serialized:
                    st.error("Deployment failed. Review the execution report above for the exact failed phase.")
                else:
                    st.warning("Deployment workflow returned, but the final deployment status could not be confirmed.")

            except requests.HTTPError as exc:

                st.error(
                    f"Orchestrator request failed: {exc}"
                )

                if exc.response is not None:
                    st.code(
                        exc.response.text,
                        language="text",
                    )

            except Exception as exc:

                st.error(
                    f"Deployment execution failed: {exc}"
                )


# ============================================================
# Architecture
# ============================================================

st.divider()

st.subheader("Secure Deployment Architecture")

st.markdown(
"""
**Browser → Streamlit → ADK Orchestrator → Specialized Agents → Agent Gateway → GCP**

- **Build Agent** — source-controlled container build through Cloud Build
- **Registry Agent** — Artifact Registry verification and immutable digest resolution
- **Hosting Agent** — Cloud Run deployment and verification
- **Agent Gateway** — authorization, least privilege and audit logging
- **Memory Bank** — persistent deployment history
"""
)
