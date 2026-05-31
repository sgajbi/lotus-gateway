from fastapi import APIRouter, Path

from app.contracts.foundation import (
    FoundationPortfolioCatalogResponse,
    FoundationWorkspaceResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.foundation_service import FoundationService
from app.services.foundation_service_factory import build_foundation_service

router = APIRouter(prefix="/api/v1/foundation", tags=["foundation"])


def _foundation_service() -> FoundationService:
    return build_foundation_service()


@router.get(
    "/portfolios",
    response_model=FoundationPortfolioCatalogResponse,
    summary="Get Foundation Portfolio Catalog",
    description=(
        "Returns a selector-ready catalog for the Foundation portfolio entry shell. "
        "Use this route to populate portfolio pickers before loading the full "
        "Foundation workspace payload. The response preserves lightweight portfolio "
        "identity metadata such as client and booking-center codes when the source "
        "publishes them."
    ),
)
async def get_foundation_portfolios() -> FoundationPortfolioCatalogResponse:
    service = _foundation_service()
    correlation_id = correlation_id_var.get()
    return await service.get_portfolio_catalog(correlation_id=correlation_id)


@router.get(
    "/portfolios/{portfolio_id}/workspace",
    response_model=FoundationWorkspaceResponse,
    summary="Get Foundation Workspace",
    description=(
        "Returns the first-paint Foundation workspace payload for a single portfolio. "
        "Use this route when the UI needs portfolio identity, valuation summary, "
        "allocation shape, top positions, readiness posture, workflow launch cues, "
        "and advisor-facing evidence of degraded upstream dependencies in one response. "
        "Gateway resolves the Core analytics reference before requesting performance so "
        "Foundation YTD return evidence is aligned to the latest complete calculable "
        "performance horizon."
    ),
)
async def get_foundation_workspace(
    portfolio_id: str = Path(
        ...,
        description="Stable portfolio identifier for the Foundation workspace to compose.",
        examples=["PF_1001"],
    ),
) -> FoundationWorkspaceResponse:
    service = _foundation_service()
    correlation_id = correlation_id_var.get()
    return await service.get_portfolio_workspace(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
    )
