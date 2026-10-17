from fastapi import APIRouter, Path, Query, Request

from app.contracts.workbench import WorkbenchPortfolio360Response
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_caller_context import (
    WORKBENCH_CALLER_OPENAPI,
    require_workbench_enrichment_authority,
)
from app.routers.workbench_snapshot_common import WORKBENCH_AS_OF_DATE_QUERY
from app.services.dpm_manage_request_authority import (
    dpm_manage_request_authority_scope,
)
from app.services.workbench_service_provider import workbench_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])

_PORTFOLIO_360_HEADER_DESCRIPTIONS = {
    "X-Caller-Application": (
        "Optional caller application for portfolio360 Performance enrichment; "
        "defaults to `lotus-gateway` when omitted or blank."
    ),
    "X-Booking-Center-Code": (
        "Optional booking-center context for portfolio360 Performance enrichment; "
        "forwarded only when provided."
    ),
}
_PORTFOLIO_360_CALLER_APPLICATION_SCHEMA = {"type": "string", "minLength": 0}
_REQUIRED_PORTFOLIO_360_HEADER_DESCRIPTION = (
    "Trusted caller context for portfolio360 enrichments; actor, tenant, region and role are "
    "required."
)


async def _get_portfolio_360(
    *,
    request: Request,
    portfolio_id: str,
    session_id: str | None,
    requested_as_of_date: str | None,
) -> WorkbenchPortfolio360Response:
    caller_headers, authority = require_workbench_enrichment_authority(request)
    service = workbench_service().with_caller_headers(caller_headers)
    with dpm_manage_request_authority_scope(authority):
        return await service.get_portfolio_360(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id_var.get(),
            session_id=session_id,
            requested_as_of_date=requested_as_of_date,
        )


@router.get(
    "/{portfolio_id}/portfolio-360",
    response_model=WorkbenchPortfolio360Response,
    summary="Get Portfolio 360",
    description=(
        "Returns the baseline position inventory plus optional projected holdings for an active "
        "sandbox session. Use this route for live position panels, sandbox comparison, and any "
        "consumer that needs the same overview context with holdings-level detail attached. The "
        "optional performance and rebalance enrichments always execute, so trusted X-Actor-Id, "
        "X-Tenant-Id, X-Region and X-Role caller context is required. Optional "
        "X-Caller-Application defaults to `lotus-gateway` when omitted or blank; optional "
        "X-Booking-Center-Code is forwarded only when provided. Repeated caller headers are "
        "refused. Caller context is admitted scope, not a production IAM grant."
    ),
    responses={400: {"description": "Missing, invalid or ambiguous enrichment caller context."}},
    openapi_extra={
        "parameters": [
            {
                **parameter,
                "required": str(parameter["name"])
                in {"X-Actor-Id", "X-Tenant-Id", "X-Region", "X-Role"},
                "schema": (
                    _PORTFOLIO_360_CALLER_APPLICATION_SCHEMA
                    if str(parameter["name"]) == "X-Caller-Application"
                    else parameter["schema"]
                ),
                "description": _PORTFOLIO_360_HEADER_DESCRIPTIONS.get(
                    str(parameter["name"]), _REQUIRED_PORTFOLIO_360_HEADER_DESCRIPTION
                ),
            }
            for parameter in WORKBENCH_CALLER_OPENAPI["parameters"]
        ]
    },
)
async def get_portfolio_360(
    request: Request,
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier for the portfolio-360 surface.",
        examples=["PF_1001"],
    ),
    session_id: str | None = Query(
        default=None,
        description="Optional sandbox session identifier used to overlay projected state.",
        examples=["sess_1"],
    ),
    as_of_date: str | None = WORKBENCH_AS_OF_DATE_QUERY,
) -> WorkbenchPortfolio360Response:
    return await _get_portfolio_360(
        request=request,
        portfolio_id=portfolio_id,
        session_id=session_id,
        requested_as_of_date=as_of_date,
    )
