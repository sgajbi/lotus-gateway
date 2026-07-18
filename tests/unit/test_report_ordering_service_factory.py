from app.clients.reporting_client import ReportingClient
from app.services.report_ordering_service import ReportOrderingService
from app.services.report_ordering_service_factory import (
    build_report_ordering_service,
    report_ordering_service_signature,
)


def test_report_ordering_service_factory_uses_governed_reporting_client(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.reporting_aggregation_base_url",
        "http://report:8300/",
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.upstream_timeout_seconds",
        4.0,
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.upstream_max_retries",
        3,
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.upstream_retry_backoff_seconds",
        0.25,
    )

    service = build_report_ordering_service()

    assert isinstance(service, ReportOrderingService)
    assert isinstance(service._reporting_client, ReportingClient)
    assert report_ordering_service_signature() == (
        "http://report:8300/",
        4.0,
        3,
        0.25,
    )
