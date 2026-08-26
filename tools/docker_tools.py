from __future__ import annotations

import subprocess
from pathlib import Path


MAX_OUTPUT_LENGTH = 12000


def _run_docker_command(
    args: list[str],
    working_directory: Path,
    timeout: int = 300,
) -> str:
    """
    Execute a narrowly scoped Docker CLI command.

    This helper intentionally accepts only preconstructed Docker
    arguments from the trusted tool functions below.
    """

    try:
        result = subprocess.run(
            ["docker", *args],
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return "ERROR: Docker CLI is not installed or is not available on PATH."
    except subprocess.TimeoutExpired:
        return f"ERROR: Docker command timed out after {timeout} seconds."

    output = (result.stdout + "\n" + result.stderr).strip()

    if len(output) > MAX_OUTPUT_LENGTH:
        output = output[-MAX_OUTPUT_LENGTH:]

    if result.returncode != 0:
        return (
            f"ERROR: Docker command failed with exit code "
            f"{result.returncode}.\n{output}"
        )

    return output or "Docker command completed successfully."


def docker_build(
    project_path: str,
    image_name: str,
    dockerfile: str = "Dockerfile",
) -> str:
    """
    Build a Docker image from a local application directory.

    Use this tool only after confirming that the project directory
    contains a valid Dockerfile.

    Args:
        project_path: Absolute or relative path to the application.
        image_name: Local Docker image name and tag, for example
            "secure-demo-app:v1".
        dockerfile: Dockerfile filename inside project_path.

    Returns:
        Build output and status.

    Security boundary:
        This tool only performs a local Docker build. It does not
        push images to Artifact Registry or interact with Google Cloud.
    """

    project = Path(project_path).resolve()

    if not project.exists():
        return f"ERROR: Project path does not exist: {project}"

    if not project.is_dir():
        return f"ERROR: Project path is not a directory: {project}"

    dockerfile_path = project / dockerfile

    if not dockerfile_path.exists():
        return f"ERROR: Dockerfile not found: {dockerfile_path}"

    if not image_name or "/" in image_name:
        return (
            "ERROR: image_name must be a local Docker image name "
            "such as 'secure-demo-app:v1'. Registry-qualified names "
            "are not permitted by this tool."
        )

    return _run_docker_command(
        [
            "build",
            "--file",
            dockerfile,
            "--tag",
            image_name,
            ".",
        ],
        working_directory=project,
    )


def docker_inspect(image_name: str) -> str:
    """
    Inspect a locally built Docker image.

    Args:
        image_name: Local Docker image name and tag.

    Returns:
        Docker image metadata.

    Security boundary:
        This tool only inspects local Docker images.
    """

    if not image_name or "/" in image_name:
        return (
            "ERROR: Only local image names are allowed. "
            "Registry-qualified images are not permitted."
        )

    return _run_docker_command(
        [
            "image",
            "inspect",
            image_name,
        ],
        working_directory=Path.cwd(),
        timeout=60,
    )
