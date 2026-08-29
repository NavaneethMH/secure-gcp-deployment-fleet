# Secure GCP Deployment Fleet — E2E Fix

## Why the previous deployment stopped

The Build Agent ran inside Cloud Run and called the local Docker CLI. Cloud Run does not provide the Docker daemon required by that workflow, so the execution stopped at:

`ERROR: Docker CLI is not installed or is not available on PATH.`

The fixed workflow uses Google Cloud Build for the container build. Cloud Build fetches the exact GitHub commit, builds the Docker image remotely, and publishes it to Artifact Registry. The Registry Agent then verifies the published artifact and resolves the immutable digest. The Hosting Agent deploys that digest to Cloud Run.

## 1. Apply the source changes

Replace the changed files from this patch in the local repository. Do not copy `.env`, `.git`, `.venv`, `memory/memory.db`, or audit runtime logs from an archive.

## 2. Make sure the deployment source is committed

The deployment request uses an exact Git commit SHA. The commit being deployed must contain:

- `main.py`
- `Dockerfile`
- `requirements.streamlit.txt`
- the updated fleet source files

Run from the repository root:

```powershell
git status
git add .
git commit -m "fix: use Cloud Build for secure remote container builds"
git push origin main
git rev-parse HEAD
```

Use the SHA printed by the final command in the Streamlit deployment form.

## 3. Enable required APIs

```powershell
gcloud config set project secure-gcp-deployment-fleet

gcloud services enable `
  cloudbuild.googleapis.com `
  artifactregistry.googleapis.com `
  run.googleapis.com
```

The `secure-fleet` Artifact Registry Docker repository must exist in `asia-south1`.

## 4. Give the Orchestrator permission to create builds

First identify the service account used by the deployed `orchestrator` Cloud Run service:

```powershell
$ORCH_SA = gcloud run services describe orchestrator `
  --region=asia-south1 `
  --project=secure-gcp-deployment-fleet `
  --format="value(spec.template.spec.serviceAccountName)"

$ORCH_SA
```

Grant it Cloud Build Editor:

```powershell
gcloud projects add-iam-policy-binding secure-gcp-deployment-fleet `
  --member="serviceAccount:$ORCH_SA" `
  --role="roles/cloudbuild.builds.editor"
```

## 5. Give the Cloud Build service account Artifact Registry access

Find the service account Cloud Build will use:

```powershell
$BUILD_SA = gcloud builds get-default-service-account `
  --region=asia-south1 `
  --project=secure-gcp-deployment-fleet

$BUILD_SA
```

Grant the minimum build/publish permissions needed for this deployment:

```powershell
gcloud projects add-iam-policy-binding secure-gcp-deployment-fleet `
  --member="serviceAccount:$BUILD_SA" `
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding secure-gcp-deployment-fleet `
  --member="serviceAccount:$BUILD_SA" `
  --role="roles/logging.logWriter"
```

If Cloud Build reports a missing Cloud Storage permission, grant the required storage role to the same build service account rather than granting broad project Owner/Editor access.

If build creation reports `iam.serviceAccounts.actAs`, grant the Orchestrator service account permission to use the Cloud Build service account:

```powershell
gcloud iam service-accounts add-iam-policy-binding $BUILD_SA `
  --member="serviceAccount:$ORCH_SA" `
  --role="roles/iam.serviceAccountUser" `
  --project=secure-gcp-deployment-fleet
```

## 6. Redeploy the Orchestrator

The Build Agent and gateway changes run inside the Orchestrator service, so the Orchestrator must be rebuilt before testing the button.

From the repository root:

```powershell
gcloud builds submit `
  --region=asia-south1 `
  --config=cloudbuild-orchestrator.yaml `
  .
```

Then update the Cloud Run Orchestrator service with the newly built image according to the service/image command already used in the project.

Verify that the Orchestrator revision is ready before continuing.

## 7. Redeploy the Streamlit UI

The UI now sends the exact repository URL, commit SHA, GCP project, Artifact Registry repository, image name, and Dockerfile to the Orchestrator.

Build and push it:

```powershell
gcloud builds submit `
  --region=asia-south1 `
  --config=cloudbuild-streamlit.yaml `
  .
```

Then update the existing Streamlit Cloud Run service with the new image using the same deployment command/process already used for the UI.

## 8. Test the deployment button

Use:

- GitHub Owner: `NavaneethMH`
- Repository: `secure-gcp-deployment-fleet`
- Branch: `main`
- Commit SHA: the SHA printed by `git rev-parse HEAD`
- Cloud Run Service: `secure-fleet-demo`
- GCP Region: `asia-south1`
- GCP Project: `secure-gcp-deployment-fleet`

Expected path:

`Streamlit -> Orchestrator -> Build Agent -> Agent Gateway -> Cloud Build -> Artifact Registry -> Registry Agent -> Hosting Agent -> Cloud Run -> verification`

The Build Agent must no longer report any Docker CLI error.

## 9. Expected successful result

The final execution should contain all of these:

- Cloud Build: SUCCESS
- Artifact Registry image: verified
- Immutable image URI: `asia-south1-docker.pkg.dev/secure-gcp-deployment-fleet/secure-fleet/<image>@sha256:<digest>`
- Cloud Run deployment: SUCCESS
- Cloud Run revision: present
- Cloud Run URL: present
- Cloud Run verification: SUCCESS
- Overall status: SUCCESS

The Streamlit UI no longer treats the HTTP workflow response itself as proof of deployment success; it reports success only when the returned execution data contains a successful final deployment state.
