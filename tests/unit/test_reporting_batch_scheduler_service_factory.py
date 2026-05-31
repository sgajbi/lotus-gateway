from app.services.reporting_batch_scheduler_service_factory import (
    build_reporting_batch_scheduler_service,
)


def test_reporting_batch_scheduler_service_factory_wires_reporting_client(
    monkeypatch,
) -> None:
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

    service = build_reporting_batch_scheduler_service()

    assert service._reporting_client._base_url == "http://report:8000"
    assert service._reporting_client._timeout == 7.5
    assert service._reporting_client._max_retries == 5
    assert service._reporting_client._retry_backoff_seconds == 0.65
