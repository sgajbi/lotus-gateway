from app.services.workbench_service_provider import (
    advisor_brief_service,
    performance_workspace_service,
    risk_workspace_service,
    workbench_service,
)


def test_workbench_service_provider_reuses_services_for_unchanged_signature(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_query_base_url",
        "http://core-query-workbench-cache:8001",
    )

    first = workbench_service()
    second = workbench_service()

    assert first is second


def test_workbench_service_provider_rebuilds_when_core_routing_changes(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_query_base_url",
        "http://core-query-workbench-a:8001",
    )
    first = workbench_service()

    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_query_base_url",
        "http://core-query-workbench-b:8001",
    )
    second = workbench_service()

    assert first is not second
    assert second._lotus_core_query_client._query_base_url == "http://core-query-workbench-b:8001"


def test_workbench_child_providers_rebuild_when_shared_signature_changes(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_analytics_base_url",
        "http://performance-workbench-a:8000",
    )
    first_performance = performance_workspace_service()
    first_advisor_brief = advisor_brief_service()

    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_analytics_base_url",
        "http://performance-workbench-b:8000",
    )
    second_performance = performance_workspace_service()
    second_advisor_brief = advisor_brief_service()

    assert first_performance is not second_performance
    assert first_advisor_brief is not second_advisor_brief


def test_workbench_risk_provider_rebuilds_when_risk_routing_changes(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.risk_analytics_base_url",
        "http://risk-workbench-a:8000",
    )
    first = risk_workspace_service()

    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.risk_analytics_base_url",
        "http://risk-workbench-b:8000",
    )
    second = risk_workspace_service()

    assert first is not second
    assert second._risk_client._base_url == "http://risk-workbench-b:8000"
