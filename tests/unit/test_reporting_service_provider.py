from app.services.reporting_service_provider import (
    reporting_batch_control_service,
    reporting_batch_lifecycle_service,
    reporting_batch_scheduler_service,
    reporting_job_query_service,
    reporting_job_submission_service,
    reporting_portfolio_service,
)


def test_reporting_service_provider_wires_reporting_backed_services(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.reporting_aggregation_base_url",
        "http://reporting-provider:8000",
    )
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.render_service_base_url",
        "http://render-provider:8000",
    )

    assert (
        reporting_portfolio_service()._reporting_client._base_url
        == "http://reporting-provider:8000"
    )
    assert (
        reporting_job_submission_service()._reporting_client._base_url
        == "http://reporting-provider:8000"
    )
    assert (
        reporting_job_query_service()._reporting_client._base_url
        == "http://reporting-provider:8000"
    )
    assert (
        reporting_batch_control_service()._render_client._base_url == "http://render-provider:8000"
    )
    assert (
        reporting_batch_lifecycle_service()._render_client._base_url
        == "http://render-provider:8000"
    )
    assert (
        reporting_batch_scheduler_service()._reporting_client._base_url
        == "http://reporting-provider:8000"
    )


def test_reporting_service_provider_reuses_services_for_unchanged_signature(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.reporting_aggregation_base_url",
        "http://reporting-provider-cache:8000",
    )

    first = reporting_job_query_service()
    second = reporting_job_query_service()

    assert first is second


def test_reporting_service_provider_rebuilds_when_reporting_routing_changes(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.reporting_aggregation_base_url",
        "http://reporting-provider-a:8000",
    )
    first = reporting_job_submission_service()

    monkeypatch.setattr(
        "app.services.reporting_client_factory.settings.reporting_aggregation_base_url",
        "http://reporting-provider-b:8000",
    )
    second = reporting_job_submission_service()

    assert first is not second
    assert second._reporting_client._base_url == "http://reporting-provider-b:8000"
