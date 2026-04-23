from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Header, HTTPException, Path, Query, status

from app.clients.reporting_client import ReportingClient
from app.config import settings
from app.contracts.reporting import (
    PortfolioReviewJobRequest,
    ReportingPortfolioRequest,
    ReportingReviewResponse,
    ReportingSnapshotResponse,
    ReportingSummaryResponse,
    ReportJobHandleResponse,
    ReportJobStatusEventsResponse,
    ReportJobStatusResponse,
)
from app.middleware.correlation import correlation_id_var

router = APIRouter(prefix="/api/v1/reports", tags=["Reporting"])
jobs_router = APIRouter(prefix="/api/v1/report-jobs", tags=["Reporting"])

SUMMARY_REQUEST_EXAMPLES = {
    "wealthSummary": {
        "summary": "Wealth summary in portfolio base currency",
        "description": "Resolve wealth and allocation sections for one reporting date.",
        "value": {
            "asOfDate": "2026-02-24",
            "sections": ["WEALTH", "ALLOCATION"],
            "allocationDimensions": ["asset_class", "currency"],
        },
    }
}

REVIEW_REQUEST_EXAMPLES = {
    "frontOfficeReview": {
        "summary": "Front-office review payload in USD",
        "description": (
            "Resolve a review payload with holdings, transactions, performance, and risk."
        ),
        "value": {
            "asOfDate": "2026-02-24",
            "reportingCurrency": "USD",
            "sections": [
                "OVERVIEW",
                "ALLOCATION",
                "INCOME_AND_ACTIVITY",
                "HOLDINGS",
                "TRANSACTIONS",
                "PERFORMANCE",
                "RISK_ANALYTICS",
            ],
            "allocationDimensions": ["asset_class"],
            "lookThroughMode": "full",
        },
    }
}

PORTFOLIO_REVIEW_JOB_REQUEST_EXAMPLES = {
    "portfolioReviewJob": {
        "summary": "Portfolio review job request",
        "description": "Create a durable job handle for asynchronous portfolio review generation.",
        "value": {
            "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
            "as_of_date": "2026-04-22",
            "requested_output_formats": ["json"],
            "reporting_currency": "USD",
            "options": {
                "sections": ["OVERVIEW", "PERFORMANCE", "RISK_ANALYTICS"],
                "benchmark_code": "BMK_GLOBAL_BALANCED_60_40",
            },
        },
    }
}


def _reporting_client() -> ReportingClient:
    return ReportingClient(
        base_url=settings.reporting_aggregation_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )


def _caller_headers(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> dict[str, str]:
    missing = [
        name
        for name, value in {
            "X-Actor-Id": actor_id,
            "X-Tenant-Id": tenant_id,
            "X-Region": region,
        }.items()
        if not value or not value.strip()
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "missing_caller_context",
                "message": "Required caller context headers are missing.",
                "missing_headers": missing,
            },
        )
    values = {
        "X-Actor-Id": actor_id.strip() if actor_id else actor_id,
        "X-Caller-Application": caller_application or "lotus-gateway",
        "X-Tenant-Id": tenant_id.strip() if tenant_id else tenant_id,
        "X-Region": region.strip() if region else region,
        "X-Booking-Center-Code": booking_center_code,
        "X-Role": role,
    }
    return {key: value for key, value in values.items() if value}


def _raise_report_job_error(status_code: int, payload: dict[str, Any]) -> None:
    detail = payload.get("detail") if isinstance(payload, dict) else None
    error_code = detail.get("code") if isinstance(detail, dict) else None
    message = detail.get("message") if isinstance(detail, dict) else "Report job unavailable."

    if status_code == status.HTTP_400_BAD_REQUEST and error_code == "missing_idempotency_key":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "missing_idempotency_key", "message": message},
        )
    if status_code == status.HTTP_404_NOT_FOUND and error_code == "report_job_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "report_job_not_found", "message": message},
        )
    if status_code == status.HTTP_409_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": error_code or "report_job_conflict", "message": message},
        )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "report_job_upstream_unavailable",
                "message": "Report job service is unavailable.",
            },
        )


def _gateway_status_url(job_id: str) -> str:
    return f"/api/v1/report-jobs/{job_id}"


@router.get(
    "/{portfolio_id}/snapshot",
    response_model=ReportingSnapshotResponse,
    summary="Get reporting snapshot",
    description=(
        "Fetch report-ready aggregated snapshot rows from lotus-report for one portfolio and "
        "business date. Use this endpoint when the UI needs reporting-ready rows for a specific "
        "portfolio/date without requesting the larger summary or review payloads."
    ),
)
async def get_reporting_snapshot(
    portfolio_id: Annotated[
        str,
        Path(
            description="Canonical portfolio identifier for the requested reporting snapshot.",
            examples=["DEMO_DPM_EUR_001"],
        ),
    ],
    as_of_date: Annotated[
        str,
        Query(
            alias="asOfDate",
            description="Business as-of date in YYYY-MM-DD format for the reporting snapshot.",
            examples=["2026-02-24"],
        ),
    ],
) -> ReportingSnapshotResponse:
    client = _reporting_client()
    correlation_id = correlation_id_var.get()
    status_code, payload = await client.get_portfolio_snapshot(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        correlation_id=correlation_id,
    )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Reporting snapshot unavailable: {payload}",
        )

    generated_at_raw = payload.get("generatedAt")
    generated_at = datetime.now(UTC)
    if isinstance(generated_at_raw, str):
        try:
            generated_at = datetime.fromisoformat(generated_at_raw.replace("Z", "+00:00"))
        except ValueError:
            generated_at = datetime.now(UTC)

    return ReportingSnapshotResponse(
        correlationId=correlation_id,
        contractVersion=settings.contract_version,
        sourceService="lotus-report",
        portfolioId=portfolio_id,
        asOfDate=as_of_date,
        generatedAt=generated_at,
        rows=payload.get("rows", []),
    )


@router.post(
    "/{portfolio_id}/summary",
    response_model=ReportingSummaryResponse,
    summary="Get reporting summary",
    description=(
        "Fetch the lotus-report-owned portfolio summary payload for one portfolio and as-of "
        "date. Use this endpoint when the UI needs the consolidated reporting summary contract "
        "rather than the lower-level snapshot rows."
    ),
)
async def get_reporting_summary(
    portfolio_id: Annotated[
        str,
        Path(
            description="Canonical portfolio identifier for the requested reporting summary.",
            examples=["DEMO_DPM_EUR_001"],
        ),
    ],
    request: Annotated[
        ReportingPortfolioRequest,
        Body(
            description=(
                "Summary request payload forwarded to lotus-report after alias normalization. "
                "Use this when the consumer needs a report-oriented summary contract for one "
                "portfolio and business date."
            ),
            openapi_examples=SUMMARY_REQUEST_EXAMPLES,
        ),
    ],
) -> ReportingSummaryResponse:
    client = _reporting_client()
    correlation_id = correlation_id_var.get()
    request_payload = request.to_upstream_payload()
    status_code, payload = await client.post_portfolio_summary(
        portfolio_id=portfolio_id,
        payload=request_payload,
        correlation_id=correlation_id,
    )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Reporting summary unavailable: {payload}",
        )
    as_of_date = request.as_of_date
    return ReportingSummaryResponse(
        correlationId=correlation_id,
        contractVersion=settings.contract_version,
        sourceService="lotus-report",
        portfolioId=portfolio_id,
        asOfDate=as_of_date,
        data=payload,
    )


@router.post(
    "/{portfolio_id}/review",
    response_model=ReportingReviewResponse,
    summary="Get reporting review",
    description=(
        "Fetch the lotus-report-owned portfolio review payload for one portfolio and as-of "
        "date. Use this endpoint when the UI needs the report-review contract prepared for "
        "front-office or client-review workflows."
    ),
)
async def get_reporting_review(
    portfolio_id: Annotated[
        str,
        Path(
            description=(
                "Canonical portfolio identifier for the requested reporting review payload."
            ),
            examples=["DEMO_DPM_EUR_001"],
        ),
    ],
    request: Annotated[
        ReportingPortfolioRequest,
        Body(
            description=(
                "Review request payload forwarded to lotus-report after alias normalization. "
                "Use this when the consumer needs the full review-ready reporting contract "
                "for front-office or client-review workflows."
            ),
            openapi_examples=REVIEW_REQUEST_EXAMPLES,
        ),
    ],
) -> ReportingReviewResponse:
    client = _reporting_client()
    correlation_id = correlation_id_var.get()
    request_payload = request.to_upstream_payload()
    status_code, payload = await client.post_portfolio_review(
        portfolio_id=portfolio_id,
        payload=request_payload,
        correlation_id=correlation_id,
    )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Reporting review unavailable: {payload}",
        )
    as_of_date = request.as_of_date
    return ReportingReviewResponse(
        correlationId=correlation_id,
        contractVersion=settings.contract_version,
        sourceService="lotus-report",
        portfolioId=portfolio_id,
        asOfDate=as_of_date,
        data=payload,
    )


@router.post(
    "/portfolio-reviews",
    response_model=ReportJobHandleResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit portfolio review report job",
    description=(
        "Create a durable portfolio review report job through the governed gateway boundary. "
        "The response is a job handle, not a rendered document."
    ),
)
async def submit_portfolio_review_report_job(
    request: Annotated[
        PortfolioReviewJobRequest,
        Body(
            description="Portfolio review report job request.",
            openapi_examples=PORTFOLIO_REVIEW_JOB_REQUEST_EXAMPLES,
        ),
    ],
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description="Required caller idempotency key for job creation.",
        ),
    ] = None,
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> ReportJobHandleResponse:
    correlation_id = correlation_id_var.get()
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "missing_idempotency_key",
                "message": "Idempotency-Key is required.",
            },
        )

    status_code, payload = await _reporting_client().submit_portfolio_review_job(
        payload=request.model_dump(exclude_none=True, mode="json"),
        idempotency_key=idempotency_key,
        caller_headers=_caller_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id,
    )
    _raise_report_job_error(status_code, payload)
    response = ReportJobHandleResponse.model_validate(payload)
    return response.model_copy(update={"status_url": _gateway_status_url(response.report_job_id)})


@jobs_router.get(
    "/{job_id}",
    response_model=ReportJobStatusResponse,
    summary="Get report job status",
    description="Return product-safe report job status and diagnostics from lotus-report.",
)
async def get_report_job_status(
    job_id: Annotated[str, Path(description="Opaque report job identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> ReportJobStatusResponse:
    status_code, payload = await _reporting_client().get_report_job(
        job_id=job_id,
        caller_headers=_caller_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )
    _raise_report_job_error(status_code, payload)
    return ReportJobStatusResponse.model_validate(payload)


@jobs_router.get(
    "/{job_id}/events",
    response_model=ReportJobStatusEventsResponse,
    summary="Get report job event history",
    description=(
        "Return append-only report job lifecycle events through the governed gateway boundary. "
        "Use this endpoint for operational support when current status alone is insufficient."
    ),
)
async def get_report_job_events(
    job_id: Annotated[str, Path(description="Opaque report job identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> ReportJobStatusEventsResponse:
    status_code, payload = await _reporting_client().get_report_job_events(
        job_id=job_id,
        caller_headers=_caller_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )
    _raise_report_job_error(status_code, payload)
    return ReportJobStatusEventsResponse.model_validate(payload)


@jobs_router.post(
    "/{job_id}/cancel",
    response_model=ReportJobStatusResponse,
    summary="Cancel report job before render or archive",
    description="Cancel a report job while it is still before render, archive, or completion.",
)
async def cancel_report_job(
    job_id: Annotated[str, Path(description="Opaque report job identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> ReportJobStatusResponse:
    status_code, payload = await _reporting_client().cancel_report_job(
        job_id=job_id,
        caller_headers=_caller_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )
    _raise_report_job_error(status_code, payload)
    return ReportJobStatusResponse.model_validate(payload)
