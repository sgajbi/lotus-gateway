from fastapi.testclient import TestClient

from app.contracts.reporting import (
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


def test_reporting_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    assert "/api/v1/reports/{portfolio_id}/snapshot" in spec["paths"]
    assert "/api/v1/reports/{portfolio_id}/summary" in spec["paths"]
    assert "/api/v1/reports/{portfolio_id}/review" in spec["paths"]

    snapshot_path = spec["paths"]["/api/v1/reports/{portfolio_id}/snapshot"]["get"]
    summary_path = spec["paths"]["/api/v1/reports/{portfolio_id}/summary"]["post"]
    review_path = spec["paths"]["/api/v1/reports/{portfolio_id}/review"]["post"]
    snapshot_schema = spec["components"]["schemas"]["ReportingSnapshotResponse"]
    summary_schema = spec["components"]["schemas"]["ReportingSummaryResponse"]
    review_schema = spec["components"]["schemas"]["ReportingReviewResponse"]

    assert snapshot_path["description"]
    assert summary_path["description"]
    assert review_path["description"]
    assert snapshot_schema["properties"]["correlationId"]["description"]
    assert snapshot_schema["properties"]["contractVersion"]["description"]
    assert snapshot_schema["properties"]["sourceService"]["description"]
    assert snapshot_schema["properties"]["portfolioId"]["description"]
    assert snapshot_schema["properties"]["asOfDate"]["description"]
    assert snapshot_schema["properties"]["generatedAt"]["description"]
    assert snapshot_schema["properties"]["rows"]["description"]
    assert summary_schema["properties"]["correlationId"]["description"]
    assert summary_schema["properties"]["contractVersion"]["description"]
    assert summary_schema["properties"]["sourceService"]["description"]
    assert summary_schema["properties"]["portfolioId"]["description"]
    assert summary_schema["properties"]["asOfDate"]["description"]
    assert summary_schema["properties"]["data"]["description"]
    assert review_schema["properties"]["correlationId"]["description"]
    assert review_schema["properties"]["contractVersion"]["description"]
    assert review_schema["properties"]["sourceService"]["description"]
    assert review_schema["properties"]["portfolioId"]["description"]
    assert review_schema["properties"]["asOfDate"]["description"]
    assert review_schema["properties"]["data"]["description"]
