from app.services.portfolio_service_provider import (
    portfolio_performance_workspace_service,
    portfolio_service,
)


def test_portfolio_service_provider_rebuilds_when_routing_signature_changes(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_query_base_url",
        "http://core-query-a:8001",
    )
    first = portfolio_service()

    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_query_base_url",
        "http://core-query-b:8001",
    )
    second = portfolio_service()

    assert first is not second
    assert second._lotus_core_query_client._query_base_url == "http://core-query-b:8001"


def test_portfolio_performance_workspace_provider_rebuilds_with_signature_change(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_analytics_base_url",
        "http://performance-a:8000",
    )
    first = portfolio_performance_workspace_service()

    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_analytics_base_url",
        "http://performance-b:8000",
    )
    second = portfolio_performance_workspace_service()

    assert first is not second
    assert second._analytics_client._base_url == "http://performance-b:8000"
