from fastapi import APIRouter, Path, Query

from app.contracts.workbench import WorkbenchAnalyticsResponse
from app.middleware.correlation import correlation_id_var
from app.services.workbench_service_provider import workbench_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


@router.get(
    "/{portfolio_id}/analytics",
    response_model=WorkbenchAnalyticsResponse,
    summary="Get Workbench Analytics",
    description=(
        "Returns lotus-performance-owned grouped delta analytics for the baseline and optional "
        "projected portfolio state, including allocation buckets, top changes, and active "
        "return context. This route intentionally carries a warning and partial-failure signal "
        "for the retired legacy risk proxy; stateful risk modules are served by the dedicated "
        "Gateway Risk BFF routes instead."
    ),
)
async def get_workbench_analytics(
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier for the legacy workbench analytics surface.",
        examples=["PF_1001"],
    ),
    period: str = Query(
        default="YTD",
        description="Analytics horizon requested for the legacy workbench analytics response.",
        examples=["YTD"],
    ),
    group_by: str = Query(
        default="ASSET_CLASS",
        description="Grouping dimension requested for allocation and change analytics.",
        examples=["ASSET_CLASS"],
    ),
    benchmark_code: str = Query(
        default="MODEL_60_40",
        description="Benchmark code requested for comparative analytics context.",
        examples=["MODEL_60_40"],
    ),
    session_id: str | None = Query(
        default=None,
        description="Optional sandbox session identifier used to compare projected state.",
        examples=["sess_1"],
    ),
) -> WorkbenchAnalyticsResponse:
    service = workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.get_workbench_analytics(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        group_by=group_by,
        benchmark_code=benchmark_code,
        session_id=session_id,
    )
