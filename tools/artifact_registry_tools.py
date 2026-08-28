from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


MAX_OUTPUT_LENGTH = 12000

LOCAL_IMAGE_PATTERN = re.compile(
    r"^[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+$"
)

PROJECT_ID_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9-]{4,28}[a-z0-9]$"
)

REPOSITORY_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._-]{0,62}$"
)

IMAGE_NAME_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._/-]{0,127}$"
)

TAG_PATTERN = re.compile(
    r"^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$"
)


def _run_command(
    command: list[str],
    cwd: Path | None = None,
    timeout: int = 300,
) -> str:
    """
    Run a controlled subprocess and return bounded output.

    The command list is constructed only by trusted tool functions.
    """

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    except FileNotFoundError:
        return (
            "ERROR: Required executable was not found: "
            f"{command[0]}"
        )

    except subprocess.TimeoutExpired:
        return (
            f"ERROR: Command timed out after {timeout} seconds."
        )

    output = (
        result.stdout + "\n" + result.stderr
    ).strip()

    if len(output) > MAX_OUTPUT_LENGTH:
        output = output[-MAX_OUTPUT_LENGTH:]

    if result.returncode != 0:
        return (
            f"ERROR: Command failed with exit code "
            f"{result.returncode}.\n{output}"
        )

    return output or "Command completed successfully."


def _resolve_docker() -> str:
    """
    Resolve the Docker CLI executable.

    Supports Windows environments where Docker may resolve
    through docker.exe.
    """

    docker = shutil.which("docker")

    if not docker:
        docker = shutil.which("docker.exe")

    return docker or ""


def _resolve_gcloud() -> str:
    """
    Resolve the Google Cloud CLI executable.

    On Windows, gcloud is commonly exposed through gcloud.cmd.
    """

    gcloud = shutil.which("gcloud")

    if not gcloud:
        gcloud = shutil.which("gcloud.cmd")

    return gcloud or ""


def validate_local_image(
    image_name: str,
) -> str:
    """
    Verify that a local Docker image exists.

    This tool does not build, tag, push, or deploy the image.
    """

    if not LOCAL_IMAGE_PATTERN.fullmatch(image_name):
        return (
            "ERROR: Only simple local image references are allowed, "
            "for example 'secure-fleet-test:v2'."
        )

    docker = _resolve_docker()

    if not docker:
        return (
            "ERROR: Docker CLI could not be resolved from PATH. "
            "Expected docker or docker.exe."
        )

    return _run_command(
        [
            docker,
            "image",
            "inspect",
            image_name,
        ],
        timeout=60,
    )


def tag_image_for_artifact_registry(
    local_image: str,
    project_id: str,
    region: str,
    repository: str,
    image_name: str,
    tag: str,
) -> str:
    """
    Tag an existing local Docker image for Google Artifact Registry.

    This tool does not build or push the image.
    """

    if not LOCAL_IMAGE_PATTERN.fullmatch(local_image):
        return (
            "ERROR: Invalid local image reference. "
            "Expected format: image-name:tag"
        )

    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        return "ERROR: Invalid Google Cloud project ID."

    if not REPOSITORY_PATTERN.fullmatch(repository):
        return (
            "ERROR: Invalid Artifact Registry repository name."
        )

    if not IMAGE_NAME_PATTERN.fullmatch(image_name):
        return "ERROR: Invalid container image name."

    if not TAG_PATTERN.fullmatch(tag):
        return "ERROR: Invalid image tag."

    docker = _resolve_docker()

    if not docker:
        return (
            "ERROR: Docker CLI could not be resolved from PATH. "
            "Expected docker or docker.exe."
        )

    registry_image = (
        f"{region}-docker.pkg.dev/"
        f"{project_id}/"
        f"{repository}/"
        f"{image_name}:{tag}"
    )

    result = _run_command(
        [
            docker,
            "tag",
            local_image,
            registry_image,
        ],
        timeout=60,
    )

    if result.startswith("ERROR:"):
        return result

    return (
        "SUCCESS: Image tagged for Artifact Registry.\n"
        f"Local image: {local_image}\n"
        f"Registry image: {registry_image}"
    )


def push_image_to_artifact_registry(
    project_id: str,
    region: str,
    repository: str,
    image_name: str,
    tag: str,
) -> str:
    """
    Push a registry-tagged Docker image to Google Artifact Registry.

    This is the primary privileged operation of the Registry Agent.
    """

    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        return "ERROR: Invalid Google Cloud project ID."

    if not REPOSITORY_PATTERN.fullmatch(repository):
        return (
            "ERROR: Invalid Artifact Registry repository name."
        )

    if not IMAGE_NAME_PATTERN.fullmatch(image_name):
        return "ERROR: Invalid container image name."

    if not TAG_PATTERN.fullmatch(tag):
        return "ERROR: Invalid image tag."

    docker = _resolve_docker()

    if not docker:
        return (
            "ERROR: Docker CLI could not be resolved from PATH. "
            "Expected docker or docker.exe."
        )

    registry_image = (
        f"{region}-docker.pkg.dev/"
        f"{project_id}/"
        f"{repository}/"
        f"{image_name}:{tag}"
    )

    return _run_command(
        [
            docker,
            "push",
            registry_image,
        ],
        timeout=600,
    )


def verify_artifact_digest(
    project_id: str,
    region: str,
    repository: str,
    image_name: str,
    tag: str,
) -> str:
    """
    Retrieve the published image digest from Artifact Registry.

    This uses the Google Cloud CLI to inspect the published artifact.

    It does not modify the repository.
    """

    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        return "ERROR: Invalid Google Cloud project ID."

    if not REPOSITORY_PATTERN.fullmatch(repository):
        return (
            "ERROR: Invalid Artifact Registry repository name."
        )

    if not IMAGE_NAME_PATTERN.fullmatch(image_name):
        return "ERROR: Invalid container image name."

    if not TAG_PATTERN.fullmatch(tag):
        return "ERROR: Invalid image tag."

    gcloud = _resolve_gcloud()

    if not gcloud:
        return (
            "ERROR: Google Cloud CLI could not be resolved from PATH. "
            "Expected gcloud or gcloud.cmd."
        )

    registry_image = (
        f"{region}-docker.pkg.dev/"
        f"{project_id}/"
        f"{repository}/"
        f"{image_name}:{tag}"
    )

    return _run_command(
        [
            gcloud,
            "artifacts",
            "docker",
            "images",
            "describe",
            registry_image,
            "--format=value(image_summary.digest)",
        ],
        timeout=120,
    )