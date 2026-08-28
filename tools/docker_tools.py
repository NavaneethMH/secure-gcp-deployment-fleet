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
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )

    except FileNotFoundError:
        return (
            "ERROR: Docker CLI is not installed or is not available "
            "on PATH."
        )

    except subprocess.TimeoutExpired:
        return (
            f"ERROR: Docker command timed out after "
            f"{timeout} seconds."
        )

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    output = (stdout + "\n" + stderr).strip()

    if len(output) > MAX_OUTPUT_LENGTH:
        output = output[-MAX_OUTPUT_LENGTH:]

    if result.returncode != 0:
        return (
            f"ERROR: Docker command failed with exit code "
            f"{result.returncode}.\n{output}"
        )

    return output or "Docker command completed successfully."


def generate_dockerfile(
    project_path: str,
    framework: str,
    runtime: str,
    startup_command: str,
    port: int,
) -> str:
    """
    Generate a Dockerfile for the approved application project.

    The generator validates that the requested application entrypoint
    actually exists before writing the Dockerfile.

    Security boundary:
        This function only writes a Dockerfile inside the supplied
        project directory. It does not build, push, or deploy anything.
    """

    project = Path(project_path).resolve()

    if not project.exists():
        return f"ERROR: Project path does not exist: {project}"

    if not project.is_dir():
        return f"ERROR: Project path is not a directory: {project}"

    if not framework:
        return "ERROR: framework is required."

    if not runtime:
        return "ERROR: runtime is required."

    if not startup_command:
        return "ERROR: startup_command is required."

    if not isinstance(port, int) or not (1 <= port <= 65535):
        return "ERROR: port must be an integer between 1 and 65535."

    framework_normalized = framework.strip().lower()
    runtime_normalized = runtime.strip().lower()

    if not runtime_normalized.startswith("python"):
        return (
            "ERROR: Python runtime is required for the supported "
            "Python application frameworks."
        )

    # ---------------------------------------------------------------
    # STREAMLIT
    # ---------------------------------------------------------------

    if framework_normalized == "streamlit":

        candidates = (
            "app.py",
            "main.py",
            "Home.py",
        )

        entrypoint = next(
            (
                candidate
                for candidate in candidates
                if (project / candidate).is_file()
            ),
            None,
        )

        if entrypoint is None:
            return (
                "ERROR: No supported Streamlit entrypoint found in "
                f"{project}. Expected one of: "
                "app.py, main.py, Home.py. "
                "Deployment preparation has been stopped."
            )

        dockerfile = f"""FROM {runtime_normalized}-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PORT={port}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {port}

CMD ["streamlit", "run", "{entrypoint}", "--server.port={port}", "--server.address=0.0.0.0", "--server.headless=true"]
"""

    # ---------------------------------------------------------------
    # FASTAPI / FLASK
    # ---------------------------------------------------------------

    elif framework_normalized in {"fastapi", "flask"}:

        # The caller must provide the actual application startup command.
        # Do not silently substitute another server.
        dockerfile = f"""FROM {runtime_normalized}-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PORT={port}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {port}

CMD ["sh", "-c", "{startup_command}"]
"""

    else:
        return (
            f"ERROR: Unsupported framework: {framework}. "
            "Supported frameworks: streamlit, fastapi, flask."
        )

    dockerfile_path = project / "Dockerfile"

    try:
        dockerfile_path.write_text(
            dockerfile,
            encoding="utf-8",
        )

    except OSError as exc:
        return (
            "ERROR: Failed to write Dockerfile: "
            f"{dockerfile_path}\n{exc}"
        )

    return (
        "SUCCESS: Dockerfile generated.\n"
        f"Path: {dockerfile_path}\n"
        f"Framework: {framework}\n"
        f"Runtime: {runtime}\n"
        f"Port: {port}\n"
        f"Entrypoint: "
        f"{entrypoint if framework_normalized == 'streamlit' else startup_command}"
    )


def docker_build(
    project_path: str,
    image_name: str,
    dockerfile: str = "Dockerfile",
) -> str:
    """
    Build a Docker image from a local application directory.

    Use this tool only after confirming that the project directory
    contains a valid Dockerfile.

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

    if not dockerfile_path.is_file():
        return f"ERROR: Dockerfile path is not a file: {dockerfile_path}"

    if not image_name:
        return "ERROR: image_name is required."

    if "/" in image_name:
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


def docker_inspect(
    image_name: str,
) -> str:
    """
    Inspect a locally built Docker image.

    Security boundary:
        This tool only inspects local Docker images.
    """

    if not image_name:
        return "ERROR: image_name is required."

    if "/" in image_name:
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
