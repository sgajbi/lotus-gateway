from fastapi import APIRouter, status

from app.contracts.portfolio import PortfolioCatalogResponse
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


async def _get_portfolios() -> PortfolioCatalogResponse:
    return await portfolio_service().get_portfolio_catalog(correlation_id=correlation_id_var.get())


@router.get(
    "/portfolios",
    response_model=PortfolioCatalogResponse,
    summary="Get portfolio catalog",
    description=(
        "Returns the sorted portfolio catalog available to the caller. Use this endpoint to "
        "discover supported portfolio identifiers and lightweight identity metadata before "
        "loading portfolio-specific workspace or book endpoints. The catalog is the strategic "
        "portfolio-picker feed and preserves routing metadata such as client, booking-center, "
        "mandate type, and upstream status when the source publishes them."
    ),
    responses={
        status.HTTP_502_BAD_GATEWAY: {
            "description": "A portfolio catalog source is unavailable or returned invalid data.",
        },
    },
)
async def get_portfolios() -> PortfolioCatalogResponse:
    return await _get_portfolios()
