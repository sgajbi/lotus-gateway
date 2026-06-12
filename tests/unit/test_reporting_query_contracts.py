from app.contracts import reporting
from app.contracts.reporting_query import (
    REPORT_JOB_LINEAGE_RESPONSE_EXAMPLE,
    REPORT_JOB_LIST_RESPONSE_EXAMPLE,
    ReportJobListResponse,
    ReportJobStatusEventsResponse,
    ReportSnapshotLineageResponse,
    ReportStatusEvent,
)


def test_reporting_query_contracts_remain_legacy_reexported() -> None:
    assert reporting.ReportJobListResponse is ReportJobListResponse
    assert reporting.ReportJobStatusEventsResponse is ReportJobStatusEventsResponse
    assert reporting.ReportSnapshotLineageResponse is ReportSnapshotLineageResponse
    assert reporting.REPORT_JOB_LIST_RESPONSE_EXAMPLE is REPORT_JOB_LIST_RESPONSE_EXAMPLE


def test_report_job_list_response_accepts_alias_payload() -> None:
    response = ReportJobListResponse(**REPORT_JOB_LIST_RESPONSE_EXAMPLE)

    assert response.count == 1
    assert response.applied_filters.portfolio_id == "PB_SG_GLOBAL_BAL_001"
    assert response.items[0].report_job_id.startswith("rjob_")
    assert response.model_dump(by_alias=True)["appliedFilters"]["portfolioId"] == (
        "PB_SG_GLOBAL_BAL_001"
    )


def test_report_snapshot_lineage_response_composes_extracted_records() -> None:
    response = ReportSnapshotLineageResponse(**REPORT_JOB_LINEAGE_RESPONSE_EXAMPLE)

    assert response.snapshot.snapshot_id.startswith("rsnap_")
    assert response.upstream_calls[0].service_name == "lotus-core"
    assert response.upstream_calls[0].failure_category == "none"


def test_report_job_status_events_response_composes_extracted_events() -> None:
    event = ReportStatusEvent(
        status_event_id="rse_1",
        report_job_id="rjob_1",
        from_status=None,
        to_status="accepted",
        event_type="job_accepted",
        message="Portfolio review report job accepted.",
        actor="advisor-123",
        created_at="2026-04-22T09:00:00Z",
        correlation_id="corr-portfolio-review-1",
        trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
    )
    response = ReportJobStatusEventsResponse(report_job_id="rjob_1", events=[event])

    assert response.events[0].event_type == "job_accepted"
