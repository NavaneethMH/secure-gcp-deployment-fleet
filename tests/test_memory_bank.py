from memory.memory_bank import MemoryBank


def test_memory_bank_creates_database(
    tmp_path,
):

    database = (
        tmp_path / "memory.db"
    )

    memory = MemoryBank(
        database
    )

    assert database.exists()

    assert memory.get_project_history(
        "test-project"
    ) == []


def test_record_and_recall_deployment(
    tmp_path,
):

    memory = MemoryBank(
        tmp_path / "memory.db"
    )

    record_id = (
        memory.record_deployment(
            project_id="test-project",
            service_name="test-service",
            region="asia-south1",
            image_uri=(
                "asia-south1-docker.pkg.dev/"
                "test-project/"
                "repo/app@sha256:abc123"
            ),
            image_digest=(
                "sha256:abc123"
            ),
            revision="test-service-00001",
            service_url=(
                "https://test-service.run.app"
            ),
            status="SUCCESS",
        )
    )

    assert record_id

    history = (
        memory.get_project_history(
            "test-project"
        )
    )

    assert len(history) == 1

    assert history[0]["service_name"] == (
        "test-service"
    )

    assert history[0]["image_digest"] == (
        "sha256:abc123"
    )


def test_latest_successful_deployment(
    tmp_path,
):

    memory = MemoryBank(
        tmp_path / "memory.db"
    )

    memory.record_deployment(
        project_id="test-project",
        service_name="test-service",
        status="FAILED",
        error="Previous build failed.",
    )

    memory.record_deployment(
        project_id="test-project",
        service_name="test-service",
        status="SUCCESS",
        revision="test-service-00002",
    )

    latest = (
        memory.get_latest_successful_deployment(
            "test-project",
            "test-service",
        )
    )

    assert latest is not None

    assert latest["status"] == "SUCCESS"

    assert latest["revision"] == (
        "test-service-00002"
    )


def test_latest_failure(
    tmp_path,
):

    memory = MemoryBank(
        tmp_path / "memory.db"
    )

    memory.record_deployment(
        project_id="test-project",
        service_name="test-service",
        status="FAILED",
        error="Docker build failed.",
    )

    failure = (
        memory.get_latest_failure(
            "test-project",
            "test-service",
        )
    )

    assert failure is not None

    assert failure["status"] == "FAILED"

    assert failure["error"] == (
        "Docker build failed."
    )


def test_service_history_is_isolated(
    tmp_path,
):

    memory = MemoryBank(
        tmp_path / "memory.db"
    )

    memory.record_deployment(
        project_id="test-project",
        service_name="service-a",
        status="SUCCESS",
    )

    memory.record_deployment(
        project_id="test-project",
        service_name="service-b",
        status="SUCCESS",
    )

    history = (
        memory.get_service_history(
            "test-project",
            "service-a",
        )
    )

    assert len(history) == 1

    assert history[0]["service_name"] == (
        "service-a"
    )
