from fastapi import APIRouter, Path, Query

from app.contracts.workbench import WorkbenchOverviewResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_snapshot_common import WORKBENCH_AS_OF_DATE_QUERY
from app.services.workbench_service_provider import workbench_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


async def _get_workbench_overview(
    *,
    portfolio_id: str,
    requested_as_of_date: str | None,
    include_performance_snapshot: bool,
    include_rebalance_snapshot: bool,
) -> WorkbenchOverviewResponse:
    service = workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.get_workbench_overview(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        include_performance_snapshot=include_performance_snapshot,
        include_rebalance_snapshot=include_rebalance_snapshot,
        requested_as_of_date=requested_as_of_date,
    )


@router.get(
    "/{portfolio_id}/overview",
    response_model=WorkbenchOverviewResponse,
    summary="Get Workbench Overview",
    description=(
        "Returns the legacy first-paint workbench overview for shells that only need "
        "portfolio identity, headline valuation, latest performance snapshot, and latest "
        "rebalance status. Use `portfolio-360` when the caller also needs current positions "
        "or a sandbox-aware projected state."
    ),
)
async def get_workbench_overview(
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier for the legacy workbench overview surface.",
        examples=["PF_1001"],
    ),
    as_of_date: str | None = WORKBENCH_AS_OF_DATE_QUERY,
    include_performance_snapshot: bool = Query(
        default=True,
        description=(
            "Include optional performance context. Set false when the caller needs only "
            "source-confirmed portfolio valuation facts and must isolate them from analytics "
            "availability."
        ),
        examples=[True],
    ),
    include_rebalance_snapshot: bool = Query(
        default=True,
        description=(
            "Include optional rebalance workflow context. Set false when the caller needs only "
            "source-confirmed portfolio valuation facts and must isolate them from workflow "
            "availability."
        ),
        examples=[True],
    ),
) -> WorkbenchOverviewResponse:
    return await _get_workbench_overview(
        portfolio_id=portfolio_id,
        requested_as_of_date=as_of_date,
        include_performance_snapshot=include_performance_snapshot,
        include_rebalance_snapshot=include_rebalance_snapshot,
    )
