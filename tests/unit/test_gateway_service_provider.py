from app.services.gateway_service_provider import (
    archive_document_service,
    composite_performance_service,
    domain_product_catalog_service,
    idea_service,
    intake_service,
    source_product_service,
)


def test_gateway_service_provider_wires_smaller_route_services(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.archive_client_factory.settings.archive_service_base_url",
        "http://archive-provider:8000",
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_analytics_base_url",
        "http://performance-provider:8000",
    )
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_query_base_url",
        "http://core-query-provider:8001",
    )
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_ingestion_base_url",
        "http://core-ingestion-provider:8000",
    )
    monkeypatch.setattr(
        "app.services.idea_client_factory.settings.idea_service_base_url",
        "http://idea-provider:8000",
    )

    assert archive_document_service()._archive_client._base_url == "http://archive-provider:8000"
    assert (
        composite_performance_service()._analytics_client._base_url
        == "http://performance-provider:8000"
    )
    assert domain_product_catalog_service()._catalog_path is not None
    assert (
        source_product_service()._lotus_core_query_client._query_base_url
        == "http://core-query-provider:8001"
    )
    assert (
        intake_service()._lotus_core_ingestion_client._base_url
        == "http://core-ingestion-provider:8000"
    )
    assert idea_service()._idea_client._base_url == "http://idea-provider:8000"


def test_gateway_service_provider_reuses_services_for_unchanged_signature(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.archive_client_factory.settings.archive_service_base_url",
        "http://archive-provider-cache:8000",
    )

    first = archive_document_service()
    second = archive_document_service()

    assert first is second


def test_gateway_service_provider_rebuilds_when_core_query_routing_changes(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_query_base_url",
        "http://core-query-provider-a:8001",
    )
    first = source_product_service()

    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_query_base_url",
        "http://core-query-provider-b:8001",
    )
    second = source_product_service()

    assert first is not second
    assert second._lotus_core_query_client._query_base_url == "http://core-query-provider-b:8001"
