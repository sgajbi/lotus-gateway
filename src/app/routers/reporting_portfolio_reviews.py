from typing import Annotated

from fastapi import APIRouter, Body, Path

from app.contracts.reporting import ReportingPortfolioRequest, ReportingReviewResponse
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_examples import REVIEW_REQUEST_EXAMPLES
from app.services.reporting_service_provider import reporting_portfolio_service

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


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
    correlation_id = correlation_id_var.get()
    return await reporting_portfolio_service().get_review(
        portfolio_id=portfolio_id,
        request=request,
        correlation_id=correlation_id,
    )
