from app.services.intake_service_factory import build_intake_service


def test_intake_service_factory_wires_core_ingestion_and_query_clients(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_ingestion_base_url",
        "http://core-ingestion:8000",
    )
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_query_base_url",
        "http://core-query:8001",
    )
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_control_plane_base_url",
        "http://core-control:8002",
    )
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.upstream_timeout_seconds",
        6.5,
    )
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.upstream_max_retries",
        4,
    )
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.upstream_retry_backoff_seconds",
        0.75,
    )

    service = build_intake_service()

    assert service._lotus_core_ingestion_client._base_url == "http://core-ingestion:8000"
    assert service._lotus_core_ingestion_client._timeout == 6.5
    assert service._lotus_core_ingestion_client._max_retries == 4
    assert service._lotus_core_ingestion_client._retry_backoff_seconds == 0.75
    assert service._lotus_core_query_client._query_base_url == "http://core-query:8001"
    assert service._lotus_core_query_client._control_plane_base_url == "http://core-control:8002"
    assert service._lotus_core_query_client._timeout == 6.5
    assert service._lotus_core_query_client._max_retries == 4
    assert service._lotus_core_query_client._retry_backoff_seconds == 0.75
