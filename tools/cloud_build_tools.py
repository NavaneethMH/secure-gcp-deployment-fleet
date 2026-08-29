from __future__ import annotations

import re
from urllib.parse import urlparse

PROJECT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{4,28}[a-z0-9]$")
REGION_PATTERN = re.compile(r"^[a-z0-9-]{1,32}$")
REPOSITORY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,62}$")
IMAGE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._/-]{0,127}$")
TAG_PATTERN = re.compile(r"^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-fA-F]{7,64}$")
DOCKERFILE_PATTERN = re.compile(r"^[A-Za-z0-9._/-]{1,160}$")


def _valid_public_git_url(repository_url: str) -> bool:
    parsed = urlparse(repository_url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        return False
    if not parsed.path.endswith(".git"):
        return False
    return len(parsed.path.strip("/").split("/")) == 2


def submit_cloud_build(
    repository_url: str,
    commit_sha: str,
    project_id: str,
    region: str,
    artifact_repository: str,
    image_name: str,
    dockerfile: str = "Dockerfile",
    image_tag: str = "",
) -> str:
    """
    Build a GitHub revision remotely with Google Cloud Build.

    Cloud Build performs the Docker build and publishes the resulting
    image to Artifact Registry. No Docker daemon or Docker CLI is required
    inside the Orchestrator/Build Agent runtime.

    Security boundary:
        - only HTTPS GitHub repositories are accepted
        - the revision must be a commit SHA
        - the destination is restricted to the supplied project/region
        - the image is always published through Cloud Build
    """

    if not _valid_public_git_url(repository_url):
        return (
            "ERROR: repository_url must be a public HTTPS GitHub repository "
            "URL ending in .git."
        )

    if not COMMIT_PATTERN.fullmatch(commit_sha or ""):
        return "ERROR: commit_sha must be a 7-64 character hexadecimal commit SHA."

    if not PROJECT_ID_PATTERN.fullmatch(project_id or ""):
        return "ERROR: Invalid Google Cloud project ID."

    if not REGION_PATTERN.fullmatch(region or ""):
        return "ERROR: Invalid Cloud Build region."

    if not REPOSITORY_PATTERN.fullmatch(artifact_repository or ""):
        return "ERROR: Invalid Artifact Registry repository name."

    if not IMAGE_PATTERN.fullmatch(image_name or ""):
        return "ERROR: Invalid container image name."

    if not DOCKERFILE_PATTERN.fullmatch(dockerfile or ""):
        return "ERROR: Invalid Dockerfile path."

    # Do not allow absolute paths or traversal in a source-controlled path.
    if dockerfile.startswith(("/", "\\")) or ".." in dockerfile.split("/"):
        return "ERROR: Dockerfile path must remain inside the repository."

    if image_tag:
        if not TAG_PATTERN.fullmatch(image_tag):
            return "ERROR: Invalid image tag."
        tag = image_tag
    else:
        tag = commit_sha[:12].lower()

    image_uri = (
        f"{region}-docker.pkg.dev/"
        f"{project_id}/{artifact_repository}/{image_name}:{tag}"
    )

    from google.cloud.devtools import cloudbuild_v1

    build = cloudbuild_v1.Build(
        source=cloudbuild_v1.Source(
            git_source=cloudbuild_v1.GitSource(
                url=repository_url,
                revision=commit_sha,
            )
        ),
        steps=[
            cloudbuild_v1.BuildStep(
                name="gcr.io/cloud-builders/docker",
                args=[
                    "build",
                    "--file",
                    dockerfile,
                    "--tag",
                    image_uri,
                    ".",
                ],
            )
        ],
        images=[image_uri],
    )

    try:
        client = cloudbuild_v1.CloudBuildClient()
        operation = client.create_build(
            request=cloudbuild_v1.CreateBuildRequest(
                parent=f"projects/{project_id}/locations/{region}",
                project_id=project_id,
                build=build,
            )
        )

        result = operation.result(timeout=1200)

        status_name = result.status.name if result.status else "UNKNOWN"
        build_id = result.id or result.name or "unknown"

        if status_name != "SUCCESS":
            detail = result.status_detail or "No build failure detail was returned."
            return (
                "ERROR: Cloud Build failed.\n"
                f"Build ID: {build_id}\n"
                f"Status: {status_name}\n"
                f"Detail: {detail}"
            )

        return (
            "SUCCESS: Remote container build completed.\n"
            f"Build ID: {build_id}\n"
            f"Repository: {repository_url}\n"
            f"Commit: {commit_sha}\n"
            f"Dockerfile: {dockerfile}\n"
            f"Image: {image_uri}\n"
            "Registry publication: completed by Cloud Build."
        )

    except Exception as exc:
        return (
            "ERROR: Cloud Build submission failed.\n"
            f"Exception: {type(exc).__name__}\n"
            f"Message: {exc}"
        )


def verify_published_image(
    project_id: str,
    region: str,
    artifact_repository: str,
    image_name: str,
    image_tag: str,
) -> str:
    """Verify a Cloud Build-published image and return its immutable digest URI."""

    if not PROJECT_ID_PATTERN.fullmatch(project_id or ""):
        return "ERROR: Invalid Google Cloud project ID."
    if not REGION_PATTERN.fullmatch(region or ""):
        return "ERROR: Invalid Artifact Registry region."
    if not REPOSITORY_PATTERN.fullmatch(artifact_repository or ""):
        return "ERROR: Invalid Artifact Registry repository name."
    if not IMAGE_PATTERN.fullmatch(image_name or ""):
        return "ERROR: Invalid container image name."
    if not TAG_PATTERN.fullmatch(image_tag or ""):
        return "ERROR: Invalid image tag."

    parent = (
        f"projects/{project_id}/locations/{region}/"
        f"repositories/{artifact_repository}"
    )

    try:
        from google.cloud import artifactregistry_v1

        client = artifactregistry_v1.ArtifactRegistryClient()
        images = client.list_docker_images(parent=parent, page_size=1000)

        expected_tag = f"{image_name}:{image_tag}"

        for image in images:
            tags = set(image.tags or [])
            if expected_tag in tags or image.uri.endswith(f"/{expected_tag}"):
                return (
                    "SUCCESS: Artifact Registry image verified.\n"
                    f"Image: {expected_tag}\n"
                    f"Immutable URI: {image.uri}\n"
                    f"Digest: {image.uri.rsplit('@sha256:', 1)[-1]}"
                )

        return (
            "ERROR: Published image tag was not found in Artifact Registry.\n"
            f"Expected: {expected_tag}"
        )

    except Exception as exc:
        return (
            "ERROR: Artifact Registry verification failed.\n"
            f"Exception: {type(exc).__name__}\n"
            f"Message: {exc}"
        )
