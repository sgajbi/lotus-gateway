from fastapi import APIRouter, Query

from app.contracts.advisor_cockpit import (
    AdvisorCockpitEnvelopeResponse,
    AdvisorCockpitOwnerRole,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisor_cockpit_common import (
    ADVISOR_COCKPIT_READ_RESPONSES,
    cockpit_params,
)
from app.services.advisory_service_provider import advisor_cockpit_service

router = APIRouter(prefix="/api/v1/advisor-cockpit", tags=["advisor-cockpit"])


@router.get(
    "/supportability",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="Get Advisor Cockpit Supportability",
    description=(
        "Returns source-owned advisor cockpit supportability from lotus-advise. Gateway preserves "
        "downstream Gateway, Workbench, data-product, client-ready publication, and external "
        "communication boundaries exactly as supplied by Advise."
    ),
    responses=ADVISOR_COCKPIT_READ_RESPONSES,
)
async def get_advisor_cockpit_supportability(
    portfolio_id: str | None = Query(
        default=None,
        description="Optional portfolio identifier forwarded to lotus-advise.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
    advisor_id: str | None = Query(
        default=None,
        description="Optional advisor identifier forwarded to lotus-advise.",
        examples=["advisor_sg_001"],
    ),
    role: AdvisorCockpitOwnerRole = Query(
        default="ADVISOR",
        description="Caller role used by lotus-advise for source-owned cockpit projection.",
        examples=["ADVISOR"],
    ),
) -> AdvisorCockpitEnvelopeResponse:
    return await advisor_cockpit_service().get_supportability(
        params=cockpit_params(portfolio_id=portfolio_id, advisor_id=advisor_id, role=role),
        correlation_id=correlation_id_var.get(),
    )
