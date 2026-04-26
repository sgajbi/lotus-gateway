from fastapi.testclient import TestClient

from app.contracts.reporting import (
    BatchHandleResponse,
    BatchStatusResponse,
    BatchWorkerRunResponse,
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

    batch = BatchHandleResponse(
        batch_id="rbch_1",
        status="materialized",
        status_url="/api/v1/report-batches/rbch_1",
        idempotency_key="idem-batch-1",
        item_count=1,
    )
    batch_status = BatchStatusResponse(
        batch_id="rbch_1",
        selector_mode="explicit_portfolio_list",
        tenant_id="tenant-sg",
        region="APAC",
        materialized_portfolio_ids=["PB_SG_GLOBAL_BAL_001"],
        as_of_date="2026-04-22",
        requested_output_formats=["pdf"],
        reporting_currency="USD",
        status="materialized",
        item_count=1,
        status_counts={"materialized": 1},
        items=[
            {
                "batch_item_id": "rbci_1",
                "item_position": 1,
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "status": "materialized",
                "report_job_id": None,
                "created_at": "2026-04-22T09:00:00Z",
            }
        ],
        created_at="2026-04-22T09:00:00Z",
        updated_at="2026-04-22T09:00:00Z",
        correlation_id="corr-batch-1",
        trace_id="trace-batch-1",
    )
    batch_run = BatchWorkerRunResponse(
        batch_id="rbch_1",
        status="completed",
        batch_status_before="materialized",
        batch_status_after="completed",
        recovered_count=0,
        leased_count=1,
        dispatched_count=1,
        executed_count=1,
        report_job_ids=["rjob_1"],
        execution_results=[
            {
                "batch_item_id": "rbci_1",
                "report_job_id": "rjob_1",
                "item_status": "succeeded",
                "report_job_status": "archived",
            }
        ],
        status_url="/api/v1/report-batches/rbch_1",
    )

    assert batch.status_url == "/api/v1/report-batches/rbch_1"
    assert batch_status.items[0].portfolio_id == "PB_SG_GLOBAL_BAL_001"
    assert batch_run.report_job_ids == ["rjob_1"]


def test_reporting_request_normalizes_documented_aliases() -> None:
    request = ReportingPortfolioRequest(
        asOfDate="2026-02-24",
        reportingCurrency="USD",
        sections=["WEALTH", "ALLOCATION"],
        allocationDimensions=["asset_class", "currency"],
        lookThroughMode="direct_only",
        benchmarkCode="BMK_PB_GLOBAL_BALANCED_60_40",
        includeBenchmarks=True,
    )

    assert request.to_upstream_payload() == {
        "as_of_date": "2026-02-24",
        "reporting_currency": "USD",
        "sections": ["WEALTH", "ALLOCATION"],
        "allocation_dimensions": ["asset_class", "currency"],
        "look_through_mode": "direct_only",
        "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
        "includeBenchmarks": True,
    }


def test_reporting_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    assert "/api/v1/reports/{portfolio_id}/snapshot" in spec["paths"]
    assert "/api/v1/reports/{portfolio_id}/summary" in spec["paths"]
    assert "/api/v1/reports/{portfolio_id}/review" in spec["paths"]
    assert "/api/v1/reports/portfolio-reviews" in spec["paths"]
    assert "/api/v1/report-jobs" in spec["paths"]
    assert "/api/v1/report-jobs/{job_id}" in spec["paths"]
    assert "/api/v1/report-jobs/{job_id}/events" in spec["paths"]
    assert "/api/v1/report-jobs/{job_id}/cancel" in spec["paths"]
    assert "/api/v1/report-batches" in spec["paths"]
    assert "/api/v1/report-batches/{batch_id}" in spec["paths"]
    assert "/api/v1/report-batches/{batch_id}:pause" in spec["paths"]
    assert "/api/v1/report-batches/{batch_id}:resume" in spec["paths"]
    assert "/api/v1/report-batches/{batch_id}:cancel" in spec["paths"]
    assert "/api/v1/report-batches/{batch_id}:retry-failed" in spec["paths"]
    assert "/api/v1/report-batches/{batch_id}:recover-expired-leases" in spec["paths"]
    assert "/api/v1/report-batches/{batch_id}:run-once" in spec["paths"]

    snapshot_path = spec["paths"]["/api/v1/reports/{portfolio_id}/snapshot"]["get"]
    summary_path = spec["paths"]["/api/v1/reports/{portfolio_id}/summary"]["post"]
    review_path = spec["paths"]["/api/v1/reports/{portfolio_id}/review"]["post"]
    job_submit_path = spec["paths"]["/api/v1/reports/portfolio-reviews"]["post"]
    job_list_path = spec["paths"]["/api/v1/report-jobs"]["get"]
    job_status_path = spec["paths"]["/api/v1/report-jobs/{job_id}"]["get"]
    job_events_path = spec["paths"]["/api/v1/report-jobs/{job_id}/events"]["get"]
    job_cancel_path = spec["paths"]["/api/v1/report-jobs/{job_id}/cancel"]["post"]
    batch_create_path = spec["paths"]["/api/v1/report-batches"]["post"]
    batch_status_path = spec["paths"]["/api/v1/report-batches/{batch_id}"]["get"]
    batch_run_path = spec["paths"]["/api/v1/report-batches/{batch_id}:run-once"]["post"]
    request_schema = spec["components"]["schemas"]["ReportingPortfolioRequest"]
    snapshot_schema = spec["components"]["schemas"]["ReportingSnapshotResponse"]
    summary_schema = spec["components"]["schemas"]["ReportingSummaryResponse"]
    review_schema = spec["components"]["schemas"]["ReportingReviewResponse"]

    assert snapshot_path["description"]
    assert summary_path["description"]
    assert review_path["description"]
    assert job_submit_path["summary"] == "Submit portfolio review report job"
    assert job_list_path["summary"] == "Search report jobs for operations and support"
    assert job_status_path["summary"] == "Get report job status"
    assert job_events_path["summary"] == "Get report job event history"
    assert job_cancel_path["summary"] == "Cancel report job before render or archive"
    assert batch_create_path["summary"] == "Create report batch"
    assert batch_status_path["summary"] == "Get report batch status"
    assert batch_run_path["summary"] == "Run one bounded report batch worker pass"
    assert "RFC-" not in str(job_submit_path)
    assert "RFC-" not in str(job_list_path)
    assert "RFC-" not in str(job_status_path)
    assert "RFC-" not in str(job_events_path)
    assert "RFC-" not in str(job_cancel_path)
    for schema_name in [
        "ReportJobHandleResponse",
        "ReportJobListResponse",
        "ReportJobListItem",
        "ReportJobListFilters",
        "ReportJobErrorResponse",
        "ReportJobErrorDetail",
        "ReportJobStatusResponse",
        "ReportJobStatusEventsResponse",
        "ReportStatusEvent",
        "BatchCreateRequest",
        "PortfolioBatchCandidate",
        "BatchHandleResponse",
        "BatchStatusResponse",
        "BatchItemStatusResponse",
        "BatchControlResponse",
        "BatchRecoveryResponse",
        "BatchWorkerRunRequest",
        "BatchWorkerRunResponse",
        "BatchWorkerItemExecutionResponse",
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
    assert (
        review_path["requestBody"]["content"]["application/json"]["examples"]["frontOfficeReview"][
            "value"
        ]["benchmarkCode"]
        == "BMK_PB_GLOBAL_BALANCED_60_40"
    )
    assert request_schema["properties"]["asOfDate"]["description"]
    assert request_schema["properties"]["reportingCurrency"]["description"]
    assert request_schema["properties"]["sections"]["description"]
    assert request_schema["properties"]["allocationDimensions"]["description"]
    assert request_schema["properties"]["lookThroughMode"]["description"]
    assert request_schema["properties"]["benchmarkCode"]["description"]
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
    review_example = review_schema["properties"]["data"]["examples"][0]
    assert review_example["readiness"]["status"] == "partial"
    assert review_example["client_sections"][0]["status"] == "unavailable"
    assert review_example["advisor_sections"][0]["items"][0]["advisor_only"] is True
    assert (
        review_example["advisor_sections"][0]["items"][0]["route_targets"][0]["mutation_allowed"]
        is False
    )
