from contextlib import nullcontext

from fastapi import APIRouter, HTTPException, Path, Query, Request

from app.contracts.workbench import WorkbenchOverviewResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_caller_context import (
    WORKBENCH_CALLER_OPENAPI,
    require_unambiguous_workbench_caller_context,
)
from app.routers.workbench_snapshot_common import WORKBENCH_AS_OF_DATE_QUERY
from app.services.dpm_manage_request_authority import (
    build_dpm_manage_request_authority,
    dpm_manage_request_authority_scope,
)
from app.services.workbench_service_provider import workbench_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


async def _get_workbench_overview(
    *,
    request: Request,
    portfolio_id: str,
    requested_as_of_date: str | None,
    include_performance_snapshot: bool,
    include_rebalance_snapshot: bool,
) -> WorkbenchOverviewResponse:
    # Admit every requested producer boundary before any service I/O. Source-only
    # callers need neither seam and must retain the #678 compatibility contract.
    authority = None
    caller_headers: dict[str, str] = {}
    if include_performance_snapshot or include_rebalance_snapshot:
        for parameter in WORKBENCH_CALLER_OPENAPI["parameters"]:
            if len(request.headers.getlist(str(parameter["name"]))) > 1:
                raise HTTPException(400, detail={"code": "ambiguous_caller_context"})
        if include_performance_snapshot:
            caller_headers = require_unambiguous_workbench_caller_context(request)
        if include_rebalance_snapshot:
            authority = build_dpm_manage_request_authority(
                actor_id=request.headers.get("X-Actor-Id"),
                tenant_id=request.headers.get("X-Tenant-Id"),
                role=request.headers.get("X-Role"),
                region=request.headers.get("X-Region"),
            )
    service = workbench_service()
    if include_performance_snapshot:
        service = service.with_caller_headers(caller_headers)
    with dpm_manage_request_authority_scope(authority) if authority else nullcontext():
        return await service.get_workbench_overview(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id_var.get(),
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
        "or a sandbox-aware projected state. With `include_performance_snapshot=true`, "
        "trusted X-Actor-Id, X-Tenant-Id and X-Region are required. With "
        "`include_rebalance_snapshot=true`, trusted X-Actor-Id, X-Tenant-Id and X-Role "
        "are required; X-Region is forwarded when present. Repeated caller headers are "
        "refused. Both flags false preserves source-only reads without a new caller "
        "identity requirement. Caller context is admitted scope, not a production IAM grant."
    ),
    responses={400: {"description": "Missing, invalid or ambiguous optional-enrichment context."}},
    openapi_extra={
        "parameters": [
            {
                **parameter,
                "required": False,
                "description": (
                    "Trusted optional-enrichment caller context; required conditionally as "
                    "described by include_performance_snapshot and include_rebalance_snapshot."
                ),
            }
            for parameter in WORKBENCH_CALLER_OPENAPI["parameters"]
        ]
    },
)
async def get_workbench_overview(
    request: Request,
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
        request=request,
        portfolio_id=portfolio_id,
        requested_as_of_date=as_of_date,
        include_performance_snapshot=include_performance_snapshot,
        include_rebalance_snapshot=include_rebalance_snapshot,
    )
