from app.contracts import reporting
from app.contracts.reporting_batch_materialization import (
    BatchControlResponse as MaterializationBatchControlResponse,
)
from app.contracts.reporting_batch_materialization import (
    BatchCreateRequest as MaterializationBatchCreateRequest,
)
from app.contracts.reporting_batch_materialization import (
    BatchHandleResponse as MaterializationBatchHandleResponse,
)
from app.contracts.reporting_batch_materialization import (
    BatchItemStatusResponse as MaterializationBatchItemStatusResponse,
)
from app.contracts.reporting_batch_materialization import (
    BatchRecoveryResponse as MaterializationBatchRecoveryResponse,
)
from app.contracts.reporting_batch_materialization import (
    BatchStatusResponse as MaterializationBatchStatusResponse,
)
from app.contracts.reporting_batch_scheduler import (
    BatchScheduleListResponse as SchedulerBatchScheduleListResponse,
)
from app.contracts.reporting_batch_scheduler import (
    BatchSchedulerRunRequest as SchedulerBatchSchedulerRunRequest,
)
from app.contracts.reporting_batch_scheduler import (
    BatchSchedulerRunResponse as SchedulerBatchSchedulerRunResponse,
)
from app.contracts.reporting_batch_worker import (
    BatchWorkerRunRequest as WorkerBatchWorkerRunRequest,
)
from app.contracts.reporting_batch_worker import (
    BatchWorkerRunResponse as WorkerBatchWorkerRunResponse,
)
from app.contracts.reporting_batches import (
    BatchControlResponse,
    BatchCreateRequest,
    BatchHandleResponse,
    BatchItemStatusResponse,
    BatchRecoveryResponse,
    BatchScheduleListResponse,
    BatchSchedulerRunRequest,
    BatchSchedulerRunResponse,
    BatchStatusResponse,
    BatchWorkerRunRequest,
    BatchWorkerRunResponse,
    PortfolioBatchCandidate,
    RenderSupportabilitySummary,
    ReportingEvidenceSurfaceSupportability,
)
from app.contracts.reporting_errors import (
    REPORT_BATCH_ERROR_EXAMPLES,
    REPORT_JOB_ERROR_EXAMPLES,
)


def test_reporting_batch_contracts_remain_compatibility_reexports() -> None:
    assert reporting.BatchControlResponse is BatchControlResponse
    assert reporting.BatchCreateRequest is BatchCreateRequest
    assert reporting.BatchHandleResponse is BatchHandleResponse
    assert reporting.BatchItemStatusResponse is BatchItemStatusResponse
    assert reporting.BatchRecoveryResponse is BatchRecoveryResponse
    assert reporting.BatchScheduleListResponse is BatchScheduleListResponse
    assert reporting.BatchSchedulerRunRequest is BatchSchedulerRunRequest
    assert reporting.BatchSchedulerRunResponse is BatchSchedulerRunResponse
    assert reporting.BatchStatusResponse is BatchStatusResponse
    assert reporting.BatchWorkerRunRequest is BatchWorkerRunRequest
    assert reporting.BatchWorkerRunResponse is BatchWorkerRunResponse
    assert reporting.PortfolioBatchCandidate is PortfolioBatchCandidate
    assert reporting.RenderSupportabilitySummary is RenderSupportabilitySummary
    assert (
        reporting.ReportingEvidenceSurfaceSupportability is ReportingEvidenceSurfaceSupportability
    )
    assert reporting.REPORT_BATCH_ERROR_EXAMPLES is REPORT_BATCH_ERROR_EXAMPLES
    assert reporting.REPORT_JOB_ERROR_EXAMPLES is REPORT_JOB_ERROR_EXAMPLES
    assert BatchControlResponse is MaterializationBatchControlResponse
    assert BatchCreateRequest is MaterializationBatchCreateRequest
    assert BatchHandleResponse is MaterializationBatchHandleResponse
    assert BatchItemStatusResponse is MaterializationBatchItemStatusResponse
    assert BatchRecoveryResponse is MaterializationBatchRecoveryResponse
    assert BatchScheduleListResponse is SchedulerBatchScheduleListResponse
    assert BatchSchedulerRunRequest is SchedulerBatchSchedulerRunRequest
    assert BatchSchedulerRunResponse is SchedulerBatchSchedulerRunResponse
    assert BatchStatusResponse is MaterializationBatchStatusResponse
    assert BatchWorkerRunRequest is WorkerBatchWorkerRunRequest
    assert BatchWorkerRunResponse is WorkerBatchWorkerRunResponse


def test_batch_request_accepts_extracted_candidate_contract() -> None:
    request = BatchCreateRequest(
        selector_mode="explicit_portfolio_list",
        portfolio_ids=["PB_SG_GLOBAL_BAL_001"],
        source_candidates=[
            PortfolioBatchCandidate(
                portfolio_id="PB_SG_GLOBAL_BAL_001",
                tenant_id="tenant-sg",
                region="APAC",
                active=True,
                selected=True,
            )
        ],
        as_of_date="2026-04-22",
        requested_output_formats=["pdf"],
        reporting_currency="USD",
        options={"sections": ["OVERVIEW"]},
        max_batch_size=250,
    )

    assert request.source_candidates[0].portfolio_id == "PB_SG_GLOBAL_BAL_001"
    assert request.source_candidates[0].source_system == "lotus-core"


def test_batch_response_accepts_extracted_supportability_contracts() -> None:
    supportability = ReportingEvidenceSurfaceSupportability(
        state="ready",
        reason="evidence_surface_ready",
        freshness_bucket="current",
        evidence_feature_count=14,
        ready_evidence_feature_count=14,
        degraded_evidence_feature_count=0,
        workflow_count=4,
        ready_workflow_count=4,
    )
    render_supportability = RenderSupportabilitySummary(
        state="ready",
        reason="render_supportability_ready",
        freshness_bucket="current",
        deterministic_output_supported=True,
        render_store_ready=True,
        template_registry_ready=True,
        default_output_format="pdf",
        supported_output_formats=["pdf"],
    )

    response = BatchHandleResponse(
        batch_id="rbch_1",
        status="materialized",
        status_url="/api/v1/report-batches/rbch_1",
        idempotency_key="idem-batch-1",
        item_count=1,
        supportability=supportability,
        render_supportability=render_supportability,
    )

    assert response.supportability is supportability
    assert response.render_supportability is render_supportability
    assert response.model_dump()["status"] == "materialized"
