from app.services.reporting_batch_lifecycle_service_factory import (
    build_reporting_batch_lifecycle_service,
)


def test_reporting_batch_lifecycle_service_factory_wires_reporting_and_render_clients(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.reporting_aggregation_base_url",
        "http://report:8000/",
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.render_service_base_url",
        "http://render:8000/",
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

    service = build_reporting_batch_lifecycle_service()

    assert service._reporting_client._base_url == "http://report:8000"
    assert service._reporting_client._timeout == 7.5
    assert service._reporting_client._max_retries == 5
    assert service._reporting_client._retry_backoff_seconds == 0.65
    assert service._render_client._base_url == "http://render:8000"
    assert service._render_client._timeout == 7.5
    assert service._render_client._max_retries == 5
    assert service._render_client._retry_backoff_seconds == 0.65
