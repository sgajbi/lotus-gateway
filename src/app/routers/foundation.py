from fastapi import APIRouter, Path

from app.clients.dpm_client import DpmClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.clients.reporting_client import ReportingClient
from app.config import settings
from app.contracts.foundation import (
    FoundationPortfolioCatalogResponse,
    FoundationWorkspaceResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.foundation_service import FoundationService

router = APIRouter(prefix="/api/v1/foundation", tags=["foundation"])


def _foundation_service() -> FoundationService:
    dpm_base_url = (
        settings.management_service_base_url
        if settings.manage_split_enabled
        else settings.decisioning_service_base_url
    )
    return FoundationService(
        lotus_core_query_client=LotusCoreQueryClient(
            base_url=settings.portfolio_data_query_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            control_plane_base_url=settings.portfolio_data_control_plane_base_url,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        analytics_client=LotusAnalyticsClient(
            base_url=settings.performance_analytics_base_url,
            timeout_seconds=settings.performance_analytics_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        dpm_client=DpmClient(
            base_url=dpm_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        reporting_client=ReportingClient(
            base_url=settings.reporting_aggregation_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
    )


@router.get(
    "/portfolios",
    response_model=FoundationPortfolioCatalogResponse,
    summary="Get Foundation Portfolio Catalog",
    description=(
        "Returns a selector-ready catalog for the Foundation portfolio entry shell. "
        "Use this route to populate portfolio pickers before loading the full "
        "Foundation workspace payload."
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
        "and advisor-facing evidence of degraded upstream dependencies in one response."
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
