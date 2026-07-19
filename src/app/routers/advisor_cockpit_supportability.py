from fastapi import APIRouter, Query

from app.contracts.advisor_cockpit import AdvisorCockpitEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.advisor_cockpit_common import (
    ADVISOR_COCKPIT_READ_RESPONSES,
    cockpit_params,
)
from app.routers.advisor_cockpit_request import (
    AdvisorCockpitCaller,
    authorize_advisor_cockpit_request,
)
from app.services.advisor_cockpit_access_policy import ADVISOR_COCKPIT_READ_CAPABILITY
from app.services.advisory_service_provider import advisor_cockpit_service

router = APIRouter(prefix="/api/v1/advisor-cockpit", tags=["advisor-cockpit"])


async def _get_advisor_cockpit_supportability(
    *,
    caller: AdvisorCockpitCaller,
    portfolio_id: str | None,
) -> AdvisorCockpitEnvelopeResponse:
    entitled_portfolio_id = authorize_advisor_cockpit_request(
        caller,
        capability=ADVISOR_COCKPIT_READ_CAPABILITY,
        portfolio_id=portfolio_id,
    )
    return await advisor_cockpit_service().get_supportability(
        params=cockpit_params(portfolio_id=entitled_portfolio_id),
        caller_headers=caller.upstream_headers(),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/supportability",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="Get Advisor Cockpit Supportability",
    description=(
        "Returns source-owned advisor cockpit supportability from lotus-advise. Gateway preserves "
        "downstream Gateway, Workbench, data-product, client-ready publication, and external "
        "communication boundaries exactly as supplied by Advise. Advisor identity and role are "
        "derived from trusted caller context."
    ),
    responses=ADVISOR_COCKPIT_READ_RESPONSES,
)
async def get_advisor_cockpit_supportability(
    caller: AdvisorCockpitCaller,
    portfolio_id: str | None = Query(
        default=None,
        description="Optional portfolio identifier forwarded to lotus-advise.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
) -> AdvisorCockpitEnvelopeResponse:
    return await _get_advisor_cockpit_supportability(
        caller=caller,
        portfolio_id=portfolio_id,
    )
