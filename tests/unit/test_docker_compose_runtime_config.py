from pathlib import Path

from scripts.ci_local_compose_project import compose_project_name


def test_gateway_compose_mounts_domain_product_artifacts_read_only() -> None:
    compose_text = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert (
        "DOMAIN_PRODUCT_CATALOG_PATH=${DOMAIN_PRODUCT_CATALOG_PATH:-"
        "/lotus-platform/generated/domain-product-catalog.json}"
    ) in compose_text
    assert (
        "DOMAIN_PRODUCT_DEPENDENCY_GRAPH_PATH=${DOMAIN_PRODUCT_DEPENDENCY_GRAPH_PATH:-"
        "/lotus-platform/generated/domain-product-dependency-graph.json}"
    ) in compose_text
    assert (
        "DOMAIN_PRODUCT_LIVE_TRUST_CERTIFICATION_PATH=${"
        "DOMAIN_PRODUCT_LIVE_TRUST_CERTIFICATION_PATH:-"
        "/lotus-platform/output/trust-certification/"
        "domain-product-live-trust-certification.json}"
    ) in compose_text
    assert (
        "IDEA_SERVICE_BASE_URL=${IDEA_SERVICE_BASE_URL:-http://host.docker.internal:8330}"
    ) in compose_text
    assert "../lotus-platform/generated:/lotus-platform/generated:ro" in compose_text
    assert (
        "../lotus-platform/output/trust-certification:/lotus-platform/output/trust-certification:ro"
    ) in compose_text


def test_ci_local_compose_cleanup_uses_an_isolated_project_identity() -> None:
    makefile_text = Path("Makefile").read_text(encoding="utf-8")

    assert (
        "CI_LOCAL_COMPOSE_PROJECT ?= $(shell python scripts/ci_local_compose_project.py)"
        in makefile_text
    )
    assert (
        'docker compose --project-name "$(CI_LOCAL_COMPOSE_PROJECT)" '
        "-f docker-compose.ci-local.yml "
        "up --build --abort-on-container-exit --exit-code-from ci-local ci-local"
    ) in makefile_text
    assert (
        'docker compose --project-name "$(CI_LOCAL_COMPOSE_PROJECT)" '
        "-f docker-compose.ci-local.yml "
        "down -v --remove-orphans"
    ) in makefile_text
    assert "docker compose -f docker-compose.ci-local.yml down" not in makefile_text


def test_ci_local_compose_project_name_is_stable_and_checkout_specific(tmp_path: Path) -> None:
    first_checkout = tmp_path / "first" / "lotus-gateway"
    second_checkout = tmp_path / "second" / "lotus-gateway"

    first_name = compose_project_name(first_checkout)

    assert first_name == compose_project_name(first_checkout)
    assert first_name != compose_project_name(second_checkout)
    assert first_name.startswith("lotus-gateway-ci-local-lotus-gateway-")
    assert first_name.replace("-", "").isalnum()
