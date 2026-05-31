from app.services.portfolio_service_factory import (
    build_portfolio_performance_workspace_service,
    build_portfolio_service,
    portfolio_service_signature,
)


def _set_common_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.portfolio_service_factory.settings.portfolio_data_query_base_url",
        "http://core-query:8001",
    )
    monkeypatch.setattr(
        "app.services.portfolio_service_factory.settings.portfolio_data_control_plane_base_url",
        "http://core-control:8002",
    )
    monkeypatch.setattr(
        "app.services.portfolio_service_factory.settings.performance_analytics_base_url",
        "http://performance:8000",
    )
    monkeypatch.setattr(
        "app.services.portfolio_service_factory.settings.management_service_base_url",
        "http://manage:8000",
    )
    monkeypatch.setattr(
        "app.services.portfolio_service_factory.settings.decisioning_service_base_url",
        "http://advise:8000",
    )
    monkeypatch.setattr(
        "app.services.portfolio_service_factory.settings.upstream_timeout_seconds",
        6.0,
    )
    monkeypatch.setattr(
        "app.services.portfolio_service_factory.settings.performance_analytics_timeout_seconds",
        7.0,
    )
    monkeypatch.setattr(
        "app.services.portfolio_service_factory.settings.upstream_max_retries",
        4,
    )
    monkeypatch.setattr(
        "app.services.portfolio_service_factory.settings.upstream_retry_backoff_seconds",
        0.5,
    )
    monkeypatch.setattr(
        "app.services.portfolio_service_factory.settings.portfolio_upstream_cache_ttl_seconds",
        31.0,
    )


def test_portfolio_service_factory_builds_configured_portfolio_service(monkeypatch) -> None:
    _set_common_settings(monkeypatch)

    service = build_portfolio_service()

    assert service._lotus_core_query_client._query_base_url == "http://core-query:8001"
    assert service._lotus_core_query_client._control_plane_base_url == "http://core-control:8002"
    assert service._analytics_client._base_url == "http://performance:8000"
    assert service._analytics_client._timeout == 7.0
    assert service._dpm_client._base_url == "http://manage:8000"
    assert service._upstream_cache._ttl_seconds == 31.0


def test_portfolio_service_factory_builds_performance_workspace_service(monkeypatch) -> None:
    _set_common_settings(monkeypatch)

    service = build_portfolio_performance_workspace_service()

    assert service._workbench_service._lotus_core_query_client._query_base_url == (
        "http://core-query:8001"
    )
    assert service._workbench_service._analytics_client._base_url == "http://performance:8000"
    assert service._workbench_service._dpm_client._base_url == "http://manage:8000"
    assert service._workbench_service._advise_client._base_url == "http://advise:8000"
    assert service._analytics_client._base_url == "http://performance:8000"
    assert service._lotus_core_query_client._query_base_url == "http://core-query:8001"
    assert service._upstream_cache._ttl_seconds == 31.0


def test_portfolio_service_signature_changes_when_routing_settings_change(monkeypatch) -> None:
    _set_common_settings(monkeypatch)

    first_signature = portfolio_service_signature()
    monkeypatch.setattr(
        "app.services.portfolio_service_factory.settings.management_service_base_url",
        "http://manage-v2:8000",
    )

    assert portfolio_service_signature() != first_signature
