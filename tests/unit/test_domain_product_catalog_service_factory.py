from app.services.domain_product_catalog_service_factory import (
    build_domain_product_catalog_service,
)


def test_domain_product_catalog_service_factory_uses_configured_artifact_paths(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.domain_product_catalog_service_factory.settings.domain_product_catalog_path",
        "generated/domain-product-catalog.json",
    )
    monkeypatch.setattr(
        "app.services.domain_product_catalog_service_factory.settings.domain_product_dependency_graph_path",
        "generated/domain-product-dependency-graph.json",
    )
    monkeypatch.setattr(
        "app.services.domain_product_catalog_service_factory.settings.domain_product_live_trust_certification_path",
        "generated/live-trust-certification.json",
    )

    service = build_domain_product_catalog_service()

    assert service._catalog_path.as_posix() == "generated/domain-product-catalog.json"
    assert (
        service._dependency_graph_path.as_posix()
        == "generated/domain-product-dependency-graph.json"
    )
    assert (
        service._live_trust_certification_path.as_posix()
        == "generated/live-trust-certification.json"
    )
