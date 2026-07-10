from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.contracts.reporting_portfolio import ReportingSnapshotResponse
from app.middleware.correlation import correlation_id_var
from app.services.reporting_service_provider import reporting_portfolio_service

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


async def _get_reporting_snapshot(
    *,
    portfolio_id: str,
    as_of_date: str,
) -> ReportingSnapshotResponse:
    correlation_id = correlation_id_var.get()
    return await reporting_portfolio_service().get_snapshot(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        correlation_id=correlation_id,
    )


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
    return await _get_reporting_snapshot(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
    )
