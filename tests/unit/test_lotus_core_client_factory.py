from app.services.lotus_core_client_factory import build_lotus_core_query_client


def test_lotus_core_query_client_factory_builds_configured_query_client(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_query_base_url",
        "http://core-query:8001/",
    )
    monkeypatch.setattr(
        "app.services.lotus_core_client_factory.settings.portfolio_data_control_plane_base_url",
        "http://core-control:8002/",
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

    client = build_lotus_core_query_client()

    assert client._query_base_url == "http://core-query:8001"
    assert client._control_plane_base_url == "http://core-control:8002"
    assert client._timeout == 6.5
    assert client._max_retries == 4
    assert client._retry_backoff_seconds == 0.75
