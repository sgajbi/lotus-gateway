from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from app.clients.reporting_client import ReportingClient
from app.config import settings
from app.contracts.reporting import (
    ReportingPortfolioRequest,
    ReportingReviewResponse,
    ReportingSnapshotResponse,
    ReportingSummaryResponse,
)
from app.middleware.correlation import correlation_id_var

router = APIRouter(prefix="/api/v1/reports", tags=["Reporting"])

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
    client = ReportingClient(
        base_url=settings.reporting_aggregation_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
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
    client = ReportingClient(
        base_url=settings.reporting_aggregation_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
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
    client = ReportingClient(
        base_url=settings.reporting_aggregation_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
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
