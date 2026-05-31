from app.services.reporting_client_factory import (
    build_render_client,
    build_reporting_client,
    render_client_signature,
    reporting_client_signature,
)


def test_reporting_client_factory_builds_governed_reporting_client(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.reporting_aggregation_base_url",
        "http://report:8000/",
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.upstream_timeout_seconds",
        7.5,
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.upstream_max_retries",
        5,
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.upstream_retry_backoff_seconds",
        0.65,
    )

    client = build_reporting_client()

    assert client._base_url == "http://report:8000"
    assert client._timeout == 7.5
    assert client._max_retries == 5
    assert client._retry_backoff_seconds == 0.65
    assert reporting_client_signature() == ("http://report:8000/", 7.5, 5, 0.65)


def test_reporting_client_factory_builds_governed_render_client(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.render_service_base_url",
        "http://render:8000/",
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.upstream_timeout_seconds",
        8.5,
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.upstream_max_retries",
        6,
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.upstream_retry_backoff_seconds",
        0.8,
    )

    client = build_render_client()

    assert client._base_url == "http://render:8000"
    assert client._timeout == 8.5
    assert client._max_retries == 6
    assert client._retry_backoff_seconds == 0.8
    assert render_client_signature() == ("http://render:8000/", 8.5, 6, 0.8)
