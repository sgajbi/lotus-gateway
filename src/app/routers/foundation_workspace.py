from fastapi import APIRouter, Path

from app.contracts.foundation import FoundationWorkspaceResponse
from app.middleware.correlation import correlation_id_var
from app.services.gateway_service_provider import foundation_service

router = APIRouter(prefix="/api/v1/foundation", tags=["foundation"])


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
    service = foundation_service()
    correlation_id = correlation_id_var.get()
    return await service.get_portfolio_workspace(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
    )
