from app.services.workbench_service_factory import (
    build_advisor_brief_service,
    build_performance_workspace_service,
    build_risk_workspace_service,
    build_workbench_service,
    workbench_service_signature,
)


def _set_common_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.portfolio_data_query_base_url",
        "http://core-query:8001",
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.portfolio_data_control_plane_base_url",
        "http://core-control:8002",
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.performance_analytics_base_url",
        "http://performance:8000",
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.risk_analytics_base_url",
        "http://risk:8000",
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.ai_service_base_url",
        "http://ai:8000",
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.management_service_base_url",
        "http://manage:8000",
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.decisioning_service_base_url",
        "http://advise:8000",
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.upstream_timeout_seconds",
        6.0,
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.performance_analytics_timeout_seconds",
        7.0,
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.ai_service_timeout_seconds",
        8.0,
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.upstream_max_retries",
        4,
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.upstream_retry_backoff_seconds",
        0.5,
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.advisor_brief_cache_ttl_seconds",
        31.0,
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.risk_bff_cache_ttl_seconds",
        41.0,
    )


def test_workbench_service_factory_builds_configured_core_performance_manage_and_advise_clients(
    monkeypatch,
) -> None:
    _set_common_settings(monkeypatch)

    service = build_workbench_service()

    assert service._lotus_core_query_client._query_base_url == "http://core-query:8001"
    assert service._lotus_core_query_client._control_plane_base_url == "http://core-control:8002"
    assert service._analytics_client._base_url == "http://performance:8000"
    assert service._analytics_client._timeout == 7.0
    assert service._dpm_client._base_url == "http://manage:8000"
    assert service._advise_client._base_url == "http://advise:8000"


def test_workbench_service_factory_wires_performance_advisor_and_risk_services(
    monkeypatch,
) -> None:
    _set_common_settings(monkeypatch)

    workbench_service = build_workbench_service()
    performance_service = build_performance_workspace_service(workbench_service)
    advisor_service = build_advisor_brief_service(performance_service)
    risk_service = build_risk_workspace_service(workbench_service)

    assert performance_service._workbench_service is workbench_service
    assert performance_service._analytics_client._base_url == "http://performance:8000"
    assert performance_service._lotus_core_query_client._query_base_url == "http://core-query:8001"
    assert advisor_service._performance_workspace_service is performance_service
    assert advisor_service._lotus_ai_client._base_url == "http://ai:8000"
    assert advisor_service._lotus_ai_client._timeout == 8.0
    assert advisor_service._advise_client._base_url == "http://advise:8000"
    assert risk_service._risk_client._base_url == "http://risk:8000"
    assert risk_service._manage_client._base_url == "http://manage:8000"
    assert risk_service._cash_source is workbench_service
    assert risk_service._cache._ttl_seconds == 41.0


def test_workbench_service_signature_changes_when_routing_settings_change(monkeypatch) -> None:
    _set_common_settings(monkeypatch)

    first_signature = workbench_service_signature()
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.management_service_base_url",
        "http://manage-v2:8000",
    )

    assert workbench_service_signature() != first_signature
