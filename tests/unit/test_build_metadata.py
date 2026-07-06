from fastapi.testclient import TestClient

from app.build_metadata import gateway_build_metadata
from app.main import app


def test_gateway_build_metadata_reads_non_secret_runtime_environment() -> None:
    metadata = gateway_build_metadata(
        {
            "LOTUS_APP_VERSION": "1.2.3",
            "LOTUS_GIT_COMMIT_SHA": "abc123",
            "LOTUS_GIT_BRANCH": "main",
            "LOTUS_BUILD_TIMESTAMP": "2026-07-06T03:00:00Z",
            "LOTUS_REPO_URL": "https://github.com/sgajbi/lotus-gateway",
            "LOTUS_IMAGE_DIGEST": "sha256:abc",
            "LOTUS_CI_RUN_ID": "123456",
        }
    )

    assert metadata == {
        "service": "lotus-gateway",
        "version": "1.2.3",
        "git_commit_sha": "abc123",
        "git_branch": "main",
        "build_timestamp": "2026-07-06T03:00:00Z",
        "repo_url": "https://github.com/sgajbi/lotus-gateway",
        "image_digest": "sha256:abc",
        "ci_run_id": "123456",
    }


def test_gateway_build_metadata_defaults_unknowns_without_secrets() -> None:
    metadata = gateway_build_metadata({})

    assert metadata["service"] == "lotus-gateway"
    assert metadata["version"] == "0.1.0"
    assert metadata["git_commit_sha"] == "unknown"
    assert "secret" not in metadata
    assert "token" not in metadata


def test_version_endpoint_exposes_build_metadata(monkeypatch) -> None:
    monkeypatch.setenv("LOTUS_GIT_COMMIT_SHA", "sha-test")
    monkeypatch.setenv("LOTUS_GIT_BRANCH", "feat/test")
    monkeypatch.setenv("LOTUS_BUILD_TIMESTAMP", "2026-07-06T04:00:00Z")
    monkeypatch.setenv("LOTUS_REPO_URL", "https://github.com/sgajbi/lotus-gateway")
    monkeypatch.setenv("LOTUS_IMAGE_DIGEST", "sha256:test")
    monkeypatch.setenv("LOTUS_CI_RUN_ID", "run-1")

    response = TestClient(app).get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "service": "lotus-gateway",
        "version": "0.1.0",
        "git_commit_sha": "sha-test",
        "git_branch": "feat/test",
        "build_timestamp": "2026-07-06T04:00:00Z",
        "repo_url": "https://github.com/sgajbi/lotus-gateway",
        "image_digest": "sha256:test",
        "ci_run_id": "run-1",
    }


def test_dockerfile_labels_build_metadata_without_secret_args() -> None:
    dockerfile = open("Dockerfile", encoding="utf-8").read()

    for fragment in (
        "org.opencontainers.image.revision",
        "org.opencontainers.image.ref.name",
        "org.opencontainers.image.created",
        "org.opencontainers.image.source",
        "org.opencontainers.image.digest",
        "com.lotus.ci.run-id",
        "LOTUS_GIT_COMMIT_SHA",
        "LOTUS_IMAGE_DIGEST",
        "pip uninstall --yes wheel jaraco.context setuptools",
    ):
        assert fragment in dockerfile

    arg_env_lines = [
        line for line in dockerfile.splitlines() if line.strip().startswith(("ARG ", "ENV "))
    ]
    assert all("SECRET" not in line.upper() for line in arg_env_lines)
    assert all("TOKEN" not in line.upper() for line in arg_env_lines)
    assert all("PASSWORD" not in line.upper() for line in arg_env_lines)
