from fastapi.testclient import TestClient

from app.contracts.reporting import (
    ReportingPortfolioRequest,
    ReportingReviewResponse,
    ReportingSnapshotResponse,
    ReportingSummaryResponse,
)
from app.main import app


def test_reporting_contract_shapes() -> None:
    snapshot = ReportingSnapshotResponse(
        correlationId="corr-reporting-1",
        contractVersion="v1",
        sourceService="lotus-report",
        portfolioId="DEMO_DPM_EUR_001",
        asOfDate="2026-02-24",
        generatedAt="2026-02-24T07:00:00Z",
        rows=[{"bucket": "TOTAL", "metric": "market_value_base", "value": 1250000.0}],
    )
    summary = ReportingSummaryResponse(
        correlationId="corr-reporting-2",
        contractVersion="v1",
        sourceService="lotus-report",
        portfolioId="DEMO_DPM_EUR_001",
        asOfDate="2026-02-24",
        data={"wealth": {"total_market_value": 123.0}},
    )
    review = ReportingReviewResponse(
        correlationId="corr-reporting-3",
        contractVersion="v1",
        sourceService="lotus-report",
        portfolioId="DEMO_DPM_EUR_001",
        asOfDate="2026-02-24",
        data={"overview": {"total_market_value": 1000.0}},
    )

    assert snapshot.source_service == "lotus-report"
    assert summary.data["wealth"]["total_market_value"] == 123.0
    assert review.data["overview"]["total_market_value"] == 1000.0


def test_reporting_request_normalizes_documented_aliases() -> None:
    request = ReportingPortfolioRequest(
        asOfDate="2026-02-24",
        reportingCurrency="USD",
        sections=["WEALTH", "ALLOCATION"],
        allocationDimensions=["asset_class", "currency"],
        lookThroughMode="direct_only",
        includeBenchmarks=True,
    )

    assert request.to_upstream_payload() == {
        "as_of_date": "2026-02-24",
        "reporting_currency": "USD",
        "sections": ["WEALTH", "ALLOCATION"],
        "allocation_dimensions": ["asset_class", "currency"],
        "look_through_mode": "direct_only",
        "includeBenchmarks": True,
    }


def test_reporting_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    assert "/api/v1/reports/{portfolio_id}/snapshot" in spec["paths"]
    assert "/api/v1/reports/{portfolio_id}/summary" in spec["paths"]
    assert "/api/v1/reports/{portfolio_id}/review" in spec["paths"]
    assert "/api/v1/reports/portfolio-reviews" in spec["paths"]
    assert "/api/v1/report-jobs/{job_id}" in spec["paths"]
    assert "/api/v1/report-jobs/{job_id}/events" in spec["paths"]
    assert "/api/v1/report-jobs/{job_id}/cancel" in spec["paths"]

    snapshot_path = spec["paths"]["/api/v1/reports/{portfolio_id}/snapshot"]["get"]
    summary_path = spec["paths"]["/api/v1/reports/{portfolio_id}/summary"]["post"]
    review_path = spec["paths"]["/api/v1/reports/{portfolio_id}/review"]["post"]
    job_submit_path = spec["paths"]["/api/v1/reports/portfolio-reviews"]["post"]
    job_status_path = spec["paths"]["/api/v1/report-jobs/{job_id}"]["get"]
    job_events_path = spec["paths"]["/api/v1/report-jobs/{job_id}/events"]["get"]
    job_cancel_path = spec["paths"]["/api/v1/report-jobs/{job_id}/cancel"]["post"]
    request_schema = spec["components"]["schemas"]["ReportingPortfolioRequest"]
    snapshot_schema = spec["components"]["schemas"]["ReportingSnapshotResponse"]
    summary_schema = spec["components"]["schemas"]["ReportingSummaryResponse"]
    review_schema = spec["components"]["schemas"]["ReportingReviewResponse"]

    assert snapshot_path["description"]
    assert summary_path["description"]
    assert review_path["description"]
    assert job_submit_path["summary"] == "Submit portfolio review report job"
    assert job_status_path["summary"] == "Get report job status"
    assert job_events_path["summary"] == "Get report job event history"
    assert job_cancel_path["summary"] == "Cancel report job before render or archive"
    assert "RFC-" not in str(job_submit_path)
    assert "RFC-" not in str(job_status_path)
    assert "RFC-" not in str(job_events_path)
    assert "RFC-" not in str(job_cancel_path)
    for schema_name in [
        "ReportJobHandleResponse",
        "ReportJobStatusResponse",
        "ReportJobStatusEventsResponse",
        "ReportStatusEvent",
    ]:
        properties = spec["components"]["schemas"][schema_name]["properties"]
        for property_contract in properties.values():
            assert property_contract.get("description")
    snapshot_parameters = {
        parameter["name"]: parameter for parameter in snapshot_path["parameters"]
    }
    summary_parameters = {parameter["name"]: parameter for parameter in summary_path["parameters"]}
    review_parameters = {parameter["name"]: parameter for parameter in review_path["parameters"]}
    assert snapshot_parameters["portfolio_id"]["description"].startswith(
        "Canonical portfolio identifier"
    )
    assert snapshot_parameters["portfolio_id"]["schema"]["examples"] == ["DEMO_DPM_EUR_001"]
    assert snapshot_parameters["asOfDate"]["description"]
    assert snapshot_parameters["asOfDate"]["schema"]["examples"] == ["2026-02-24"]
    assert summary_parameters["portfolio_id"]["description"].startswith(
        "Canonical portfolio identifier"
    )
    assert review_parameters["portfolio_id"]["description"].startswith(
        "Canonical portfolio identifier"
    )
    assert (
        summary_path["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ReportingPortfolioRequest"
    )
    assert summary_path["requestBody"]["content"]["application/json"]["examples"]["wealthSummary"][
        "value"
    ]["sections"] == ["WEALTH", "ALLOCATION"]
    assert (
        review_path["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ReportingPortfolioRequest"
    )
    assert (
        review_path["requestBody"]["content"]["application/json"]["examples"]["frontOfficeReview"][
            "value"
        ]["lookThroughMode"]
        == "full"
    )
    assert request_schema["properties"]["asOfDate"]["description"]
    assert request_schema["properties"]["reportingCurrency"]["description"]
    assert request_schema["properties"]["sections"]["description"]
    assert request_schema["properties"]["allocationDimensions"]["description"]
    assert request_schema["properties"]["lookThroughMode"]["description"]
    assert snapshot_schema["properties"]["correlationId"]["description"]
    assert snapshot_schema["properties"]["contractVersion"]["description"]
    assert snapshot_schema["properties"]["sourceService"]["description"]
    assert snapshot_schema["properties"]["portfolioId"]["description"]
    assert snapshot_schema["properties"]["asOfDate"]["description"]
    assert snapshot_schema["properties"]["generatedAt"]["description"]
    assert snapshot_schema["properties"]["rows"]["description"]
    assert snapshot_schema["properties"]["rows"]["examples"][0][0]["metric"] == "market_value_base"
    assert summary_schema["properties"]["correlationId"]["description"]
    assert summary_schema["properties"]["contractVersion"]["description"]
    assert summary_schema["properties"]["sourceService"]["description"]
    assert summary_schema["properties"]["portfolioId"]["description"]
    assert summary_schema["properties"]["asOfDate"]["description"]
    assert summary_schema["properties"]["data"]["description"]
    assert (
        summary_schema["properties"]["data"]["examples"][0]["wealth"]["total_market_value"] == 123.0
    )
    assert review_schema["properties"]["correlationId"]["description"]
    assert review_schema["properties"]["contractVersion"]["description"]
    assert review_schema["properties"]["sourceService"]["description"]
    assert review_schema["properties"]["portfolioId"]["description"]
    assert review_schema["properties"]["asOfDate"]["description"]
    assert review_schema["properties"]["data"]["description"]
    assert (
        review_schema["properties"]["data"]["examples"][0]["risk_analytics"]["volatility_30d_pct"]
        == 9.4
    )
