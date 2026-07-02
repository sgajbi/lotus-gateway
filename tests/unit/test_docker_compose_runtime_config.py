from pathlib import Path


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
