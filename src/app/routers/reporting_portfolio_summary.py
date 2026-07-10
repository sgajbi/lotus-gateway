from typing import Annotated

from fastapi import APIRouter, Body, Path

from app.contracts.reporting_portfolio import (
    ReportingPortfolioRequest,
    ReportingSummaryResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_examples import SUMMARY_REQUEST_EXAMPLES
from app.services.reporting_service_provider import (
    reporting_portfolio_service,
)

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


async def _get_reporting_summary(
    *,
    portfolio_id: str,
    request: ReportingPortfolioRequest,
) -> ReportingSummaryResponse:
    correlation_id = correlation_id_var.get()
    return await reporting_portfolio_service().get_summary(
        portfolio_id=portfolio_id,
        request=request,
        correlation_id=correlation_id,
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
    return await _get_reporting_summary(
        portfolio_id=portfolio_id,
        request=request,
    )
