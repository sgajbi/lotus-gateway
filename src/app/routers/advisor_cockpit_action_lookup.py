from fastapi import APIRouter, Path, Query

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


async def _get_advisor_cockpit_action(
    *,
    caller: AdvisorCockpitCaller,
    action_item_id: str,
    portfolio_id: str,
) -> AdvisorCockpitEnvelopeResponse:
    entitled_portfolio_id = authorize_advisor_cockpit_request(
        caller,
        capability=ADVISOR_COCKPIT_READ_CAPABILITY,
        portfolio_id=portfolio_id,
        portfolio_required=True,
    )
    return await advisor_cockpit_service().get_action(
        action_item_id=action_item_id,
        params=cockpit_params(portfolio_id=entitled_portfolio_id),
        caller_headers=caller.upstream_headers(),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/actions/{action_item_id}",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="Get Advisor Cockpit Action",
    description=(
        "Returns one source-owned advisor cockpit action item from lotus-advise. Gateway does "
        "not infer policy, memo, supportability, SLA, acknowledgement, or owner-role posture. "
        "Advisor identity and role are derived from trusted caller context."
    ),
    responses=ADVISOR_COCKPIT_READ_RESPONSES,
)
async def get_advisor_cockpit_action(
    caller: AdvisorCockpitCaller,
    action_item_id: str = Path(
        ...,
        description="Advisor cockpit action item identifier owned by lotus-advise.",
        examples=["cockpit_action_policy_review_required_001"],
    ),
    portfolio_id: str = Query(
        ...,
        description="Entitled portfolio identifier used for object-level action authorization.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
) -> AdvisorCockpitEnvelopeResponse:
    return await _get_advisor_cockpit_action(
        caller=caller,
        action_item_id=action_item_id,
        portfolio_id=portfolio_id,
    )
