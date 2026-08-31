import pytest

from app.clients.reporting_client import ReportingClient


@pytest.mark.asyncio
async def test_reporting_client_reads_source_ordering_catalogue_with_trace_context(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    async def _request_observed_fanout(**kwargs):
        captured.update(kwargs)
        return 200, {"contract_version": "report-ordering-catalogue.v1"}

    monkeypatch.setattr(
        "app.clients.reporting_client.request_observed_fanout",
        _request_observed_fanout,
    )
    client = ReportingClient(
        base_url="http://report:8300/",
        timeout_seconds=3.0,
        max_retries=1,
        retry_backoff_seconds=0.1,
    )

    status_code, payload = await client.get_report_ordering_catalogue(
        correlation_id="corr-report-ordering",
    )

    assert status_code == 200
    assert payload == {"contract_version": "report-ordering-catalogue.v1"}
    assert captured["operation"] == "report.integration.ordering-catalogue"
    assert captured["method"] == "GET"
    assert captured["url"] == "http://report:8300/integration/report-ordering-catalogue"
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["X-Correlation-Id"] == "corr-report-ordering"


@pytest.mark.asyncio
async def test_reporting_client_reads_advisor_commentary_availability(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _request_observed_fanout(**kwargs):
        captured.update(kwargs)
        return 200, {"contract_version": "advisor-commentary-availability.v1"}

    monkeypatch.setattr(
        "app.clients.reporting_client.request_observed_fanout",
        _request_observed_fanout,
    )
    client = ReportingClient(
        base_url="http://report:8300/",
        timeout_seconds=3.0,
        max_retries=1,
        retry_backoff_seconds=0.1,
    )

    status_code, payload = await client.get_advisor_commentary_availability(
        portfolio_id="portfolio-1",
        tenant_id="tenant-sg-001",
        correlation_id="corr-availability",
        as_of_date="2026-04-22",
        reporting_currency="USD",
    )

    assert status_code == 200
    assert payload == {"contract_version": "advisor-commentary-availability.v1"}
    assert captured["operation"] == "report.integration.advisor-commentary-availability"
    assert captured["method"] == "GET"
    assert captured["url"] == (
        "http://report:8300/integration/report-ordering-catalogue/advisor-commentary-availability"
    )
    assert captured["params"] == {
        "portfolio_id": "portfolio-1",
        "as_of_date": "2026-04-22",
        "reporting_currency": "USD",
    }
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["X-Correlation-Id"] == "corr-availability"
    assert headers["X-Tenant-Id"] == "tenant-sg-001"


@pytest.mark.asyncio
async def test_reporting_client_omits_unspecified_availability_filters(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _request_observed_fanout(**kwargs):
        captured.update(kwargs)
        return 200, {}

    monkeypatch.setattr(
        "app.clients.reporting_client.request_observed_fanout",
        _request_observed_fanout,
    )
    client = ReportingClient(
        base_url="http://report:8300",
        timeout_seconds=3.0,
        max_retries=1,
        retry_backoff_seconds=0.1,
    )

    await client.get_advisor_commentary_availability(
        portfolio_id="portfolio-1",
        tenant_id="tenant-sg-001",
        correlation_id="corr-availability",
    )

    assert captured["params"] == {"portfolio_id": "portfolio-1"}
