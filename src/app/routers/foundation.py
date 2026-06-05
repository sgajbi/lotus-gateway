from fastapi import APIRouter, status

from app.contracts.foundation import FoundationPortfolioCatalogResponse
from app.middleware.correlation import correlation_id_var
from app.services.gateway_service_provider import foundation_service

router = APIRouter(prefix="/api/v1/foundation", tags=["foundation"])


async def _get_foundation_portfolios() -> FoundationPortfolioCatalogResponse:
    service = foundation_service()
    correlation_id = correlation_id_var.get()
    return await service.get_portfolio_catalog(correlation_id=correlation_id)


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
    responses={
        status.HTTP_502_BAD_GATEWAY: {
            "description": "A foundation portfolio-catalog source is unavailable or invalid.",
        },
    },
)
async def get_foundation_portfolios() -> FoundationPortfolioCatalogResponse:
    return await _get_foundation_portfolios()
