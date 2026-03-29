from fastapi import APIRouter, Query

from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.config import settings
from app.contracts.portfolio import (
    PortfolioActivitySummaryResponse,
    PortfolioAllocationResponse,
    PortfolioBookResponse,
    PortfolioCatalogResponse,
    PortfolioIncomeSummaryResponse,
    PortfolioInsightsResponse,
    PortfolioLiquidityResponse,
    PortfolioPositionBookResponse,
    PortfolioProjectedCashflowResponse,
    PortfolioReadinessResponse,
    PortfolioTransactionLedgerResponse,
    PortfolioWorkflowResponse,
    PortfolioWorkspaceResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


_PORTFOLIO_SERVICE = PortfolioService(
    lotus_core_query_client=LotusCoreQueryClient(
        base_url=settings.portfolio_data_query_base_url,
        control_plane_base_url=settings.portfolio_data_control_plane_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
)


def _portfolio_service() -> PortfolioService:
    return _PORTFOLIO_SERVICE

@router.get(
    "/portfolios",
    response_model=PortfolioCatalogResponse,
    summary="Get portfolio catalog",
)
async def get_portfolios() -> PortfolioCatalogResponse:
    return await _portfolio_service().get_portfolio_catalog(
        correlation_id=correlation_id_var.get()
    )


@router.get(
    "/portfolios/{portfolio_id}/workspace",
    response_model=PortfolioWorkspaceResponse,
    summary="Get portfolio workspace summary",
)
async def get_portfolio_workspace(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
) -> PortfolioWorkspaceResponse:
    return await _portfolio_service().get_portfolio_workspace(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
    )


@router.get(
    "/portfolios/{portfolio_id}/readiness",
    response_model=PortfolioReadinessResponse,
    summary="Get portfolio readiness indicators",
)
async def get_portfolio_readiness(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
) -> PortfolioReadinessResponse:
    return await _portfolio_service().get_portfolio_readiness(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
    )


@router.get(
    "/portfolios/{portfolio_id}/insights",
    response_model=PortfolioInsightsResponse,
    summary="Get portfolio insight and exception summaries",
)
async def get_portfolio_insights(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
) -> PortfolioInsightsResponse:
    return await _portfolio_service().get_portfolio_insights(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
    )


@router.get(
    "/portfolios/{portfolio_id}/workflow",
    response_model=PortfolioWorkflowResponse,
    summary="Get prioritized portfolio workflow actions",
)
async def get_portfolio_workflow(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
) -> PortfolioWorkflowResponse:
    return await _portfolio_service().get_portfolio_workflow(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
    )


@router.get(
    "/portfolios/{portfolio_id}/book",
    response_model=PortfolioBookResponse,
    summary="Get portfolio book",
)
async def get_portfolio_book(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    include_projected: bool = Query(default=False),
) -> PortfolioBookResponse:
    return await _portfolio_service().get_portfolio_book(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
    )


@router.get(
    "/portfolios/{portfolio_id}/liquidity",
    response_model=PortfolioLiquidityResponse,
    summary="Get portfolio liquidity view",
)
async def get_portfolio_liquidity(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
) -> PortfolioLiquidityResponse:
    return await _portfolio_service().get_portfolio_liquidity(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
    )


@router.get(
    "/portfolios/{portfolio_id}/projected-cashflow",
    response_model=PortfolioProjectedCashflowResponse,
    summary="Get portfolio projected cashflow view",
)
async def get_portfolio_projected_cashflow(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    horizon_days: int = Query(default=10, ge=1, le=365),
    include_projected: bool = Query(default=True),
) -> PortfolioProjectedCashflowResponse:
    return await _portfolio_service().get_portfolio_projected_cashflow(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        horizon_days=horizon_days,
        include_projected=include_projected,
    )


@router.get(
    "/portfolios/{portfolio_id}/allocations",
    response_model=PortfolioAllocationResponse,
    summary="Get portfolio allocation views",
)
async def get_portfolio_allocations(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
) -> PortfolioAllocationResponse:
    return await _portfolio_service().get_portfolio_allocations(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
    )


@router.get(
    "/portfolios/{portfolio_id}/positions",
    response_model=PortfolioPositionBookResponse,
    summary="Get portfolio positions view",
)
async def get_portfolio_positions(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    include_projected: bool = Query(default=False),
) -> PortfolioPositionBookResponse:
    return await _portfolio_service().get_portfolio_positions(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
    )


@router.get(
    "/portfolios/{portfolio_id}/income-summary",
    response_model=PortfolioIncomeSummaryResponse,
    summary="Get portfolio income summary",
)
async def get_portfolio_income_summary(
    portfolio_id: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> PortfolioIncomeSummaryResponse:
    return await _portfolio_service().get_income_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/portfolios/{portfolio_id}/activity-summary",
    response_model=PortfolioActivitySummaryResponse,
    summary="Get portfolio activity summary",
)
async def get_portfolio_activity_summary(
    portfolio_id: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> PortfolioActivitySummaryResponse:
    return await _portfolio_service().get_activity_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/portfolios/{portfolio_id}/transactions",
    response_model=PortfolioTransactionLedgerResponse,
    summary="Get portfolio transaction ledger",
)
async def get_portfolio_transactions(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    include_projected: bool = Query(default=False),
    transaction_type: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
) -> PortfolioTransactionLedgerResponse:
    return await _portfolio_service().get_transaction_ledger(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
