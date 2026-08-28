from __future__ import annotations

from google.cloud import run_v2
from google.api_core import exceptions


def deploy_cloud_run_service(
    project_id: str,
    region: str,
    service_name: str,
    image_uri: str,
    port: int = 8080,
    cpu: str = "1",
    memory: str = "512Mi",
    min_instances: int = 0,
    max_instances: int = 10,
    public: bool = True,
) -> str:
    """
    Deploy an immutable Artifact Registry image to Cloud Run.

    This tool only performs Cloud Run deployment/update operations.
    """

    # Security: only allow images from the approved
    # Artifact Registry project and region.
    expected_prefix = (
        f"{region}-docker.pkg.dev/{project_id}/"
    )

    if not image_uri.startswith(expected_prefix):
        return (
            "ERROR: Image is outside the approved "
            "Artifact Registry project/region."
        )

    # Security: only immutable image digests are accepted.
    if "@sha256:" not in image_uri:
        return (
            "ERROR: Mutable image tags are not allowed. "
            "Use an immutable @sha256:<digest> image URI."
        )

    if not 1 <= port <= 65535:
        return "ERROR: Invalid container port."

    if min_instances < 0:
        return "ERROR: min_instances cannot be negative."

    if max_instances < 1:
        return "ERROR: max_instances must be at least 1."

    if min_instances > max_instances:
        return "ERROR: min_instances cannot exceed max_instances."

    if not project_id:
        return "ERROR: project_id is required."

    if not region:
        return "ERROR: region is required."

    if not service_name:
        return "ERROR: service_name is required."

    if not image_uri:
        return "ERROR: image_uri is required."

    client = run_v2.ServicesClient()

    service_name_path = (
        f"projects/{project_id}/"
        f"locations/{region}/"
        f"services/{service_name}"
    )

    container = run_v2.Container(
        image=image_uri,
        ports=[
            run_v2.ContainerPort(
                container_port=port
            )
        ],
        resources=run_v2.ResourceRequirements(
            limits={
                "cpu": cpu,
                "memory": memory,
            }
        ),
    )

    template = run_v2.RevisionTemplate(
        containers=[container],
    )

    try:
        # ---------------------------------------------------------
        # Existing service: UPDATE
        # ---------------------------------------------------------
        try:
            existing = client.get_service(
                name=service_name_path
            )

            existing.template = template

            existing.scaling = run_v2.ServiceScaling(
                min_instance_count=min_instances,
                max_instance_count=max_instances,
            )

            request = run_v2.UpdateServiceRequest(
                service=existing,
            )

            operation = client.update_service(
                request=request
            )

            result = operation.result()

            urls = list(result.urls)

            return (
                "SUCCESS: Existing Cloud Run service updated.\n"
                f"Service: {service_name}\n"
                f"Region: {region}\n"
                f"Image: {image_uri}\n"
                f"Revision: {result.latest_ready_revision}\n"
                f"URL: "
                f"{urls[0] if urls else 'N/A'}"
            )

        except exceptions.NotFound:

            # -----------------------------------------------------
            # New service: CREATE
            #
            # IMPORTANT:
            # service.name MUST be empty here.
            # CreateServiceRequest.service_id supplies the name.
            # -----------------------------------------------------
            service = run_v2.Service(
                template=template,
                scaling=run_v2.ServiceScaling(
                    min_instance_count=min_instances,
                    max_instance_count=max_instances,
                ),
            )

            request = run_v2.CreateServiceRequest(
                parent=(
                    f"projects/{project_id}/"
                    f"locations/{region}"
                ),
                service=service,
                service_id=service_name,
            )

            operation = client.create_service(
                request=request
            )

            result = operation.result()

            urls = list(result.urls)

            return (
                "SUCCESS: Cloud Run service created.\n"
                f"Service: {service_name}\n"
                f"Region: {region}\n"
                f"Image: {image_uri}\n"
                f"Revision: {result.latest_ready_revision}\n"
                f"URL: "
                f"{urls[0] if urls else 'N/A'}"
            )

    except Exception as exc:
        return (
            "ERROR: Cloud Run deployment failed.\n"
            f"Exception: {type(exc).__name__}\n"
            f"Message: {exc}"
        )


def get_cloud_run_service(
    project_id: str,
    region: str,
    service_name: str,
) -> str:
    """
    Retrieve and verify the status of an existing Cloud Run service.
    """

    try:
        client = run_v2.ServicesClient()

        service_name_path = (
            f"projects/{project_id}/"
            f"locations/{region}/"
            f"services/{service_name}"
        )

        service = client.get_service(
            name=service_name_path
        )

        urls = list(service.urls)

        latest_ready_revision = (
            service.latest_ready_revision
        )

        latest_created_revision = (
            service.latest_created_revision
        )

        terminal_state = (
            service.terminal_condition.state
            if service.terminal_condition
            else "UNKNOWN"
        )

        return (
            "SUCCESS: Cloud Run service verified.\n"
            f"Service: {service_name}\n"
            f"Project: {project_id}\n"
            f"Region: {region}\n"
            f"Latest Created Revision: "
            f"{latest_created_revision}\n"
            f"Latest Ready Revision: "
            f"{latest_ready_revision}\n"
            f"URL: "
            f"{urls[0] if urls else 'N/A'}\n"
            f"Reconciling: "
            f"{terminal_state}"
        )

    except Exception as exc:
        return (
            "ERROR: Cloud Run service verification failed.\n"
            f"Exception: {type(exc).__name__}\n"
            f"Message: {exc}"
        )
