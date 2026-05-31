from app.services.platform_capabilities_service_factory import (
    build_platform_capabilities_service,
)


def test_platform_capabilities_service_factory_wires_configured_sources(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_query_base_url",
        "http://core-query:8001",
    )
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_control_plane_base_url",
        "http://core-control:8002",
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_analytics_base_url",
        "http://performance:8000",
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.risk_analytics_base_url",
        "http://risk:8000",
    )
    monkeypatch.setattr(
        "app.services.advise_client_factory.settings.decisioning_service_base_url",
        "http://advise:8000",
    )
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.management_service_base_url",
        "http://manage:8000",
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.reporting_aggregation_base_url",
        "http://reporting:8000",
    )
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.upstream_timeout_seconds",
        6.0,
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_analytics_timeout_seconds",
        7.0,
    )
    monkeypatch.setattr(
        "app.services.platform_capabilities_service_factory.settings.contract_version",
        "v-test",
    )
    monkeypatch.setattr(
        "app.services.platform_capabilities_service_factory.settings.platform_capabilities_source_timeout_seconds",
        1.25,
    )

    service = build_platform_capabilities_service()

    assert service._lotus_core_query_client._query_base_url == "http://core-query:8001"
    assert service._lotus_core_query_client._control_plane_base_url == "http://core-control:8002"
    assert service._analytics_client._base_url == "http://performance:8000"
    assert service._analytics_client._timeout == 7.0
    assert service._risk_client._base_url == "http://risk:8000"
    assert service._risk_client._timeout == 6.0
    assert service._advise_client._base_url == "http://advise:8000"
    assert service._manage_client._base_url == "http://manage:8000"
    assert service._reporting_client._base_url == "http://reporting:8000"
    assert service._contract_version == "v-test"
    assert service._source_timeout_seconds == 1.25
