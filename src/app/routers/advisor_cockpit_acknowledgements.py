from fastapi import APIRouter, Header, Path, Query

from app.contracts.advisor_cockpit import (
    AdvisorCockpitAcknowledgeRequest,
    AdvisorCockpitEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisor_cockpit_common import (
    ADVISOR_COCKPIT_ACKNOWLEDGEMENT_RESPONSES,
    cockpit_params,
)
from app.routers.advisor_cockpit_request import (
    AdvisorCockpitCaller,
    authorize_advisor_cockpit_request,
)
from app.services.advisor_cockpit_access_policy import (
    ADVISOR_COCKPIT_ACKNOWLEDGE_CAPABILITY,
)
from app.services.advisory_service_provider import advisor_cockpit_service

router = APIRouter(prefix="/api/v1/advisor-cockpit", tags=["advisor-cockpit"])


async def _acknowledge_advisor_cockpit_action(
    *,
    caller: AdvisorCockpitCaller,
    request: AdvisorCockpitAcknowledgeRequest,
    action_item_id: str,
    idempotency_key: str,
    portfolio_id: str,
) -> AdvisorCockpitEnvelopeResponse:
    entitled_portfolio_id = authorize_advisor_cockpit_request(
        caller,
        capability=ADVISOR_COCKPIT_ACKNOWLEDGE_CAPABILITY,
        portfolio_id=portfolio_id,
        portfolio_required=True,
    )
    return await advisor_cockpit_service().acknowledge_action(
        action_item_id=action_item_id,
        body={
            **request.model_dump(exclude_none=True),
            "acknowledged_by": caller.actor_id,
        },
        params=cockpit_params(portfolio_id=entitled_portfolio_id),
        caller_headers=caller.upstream_headers(),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/actions/{action_item_id}/acknowledgements",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="Acknowledge Advisor Cockpit Action",
    description=(
        "Records an idempotent acknowledgement through lotus-advise. Gateway forwards the "
        "observed action version and idempotency key, and does not clear blocking policy, memo, "
        "supportability, owner-role, or client-ready posture locally. The acknowledging actor is "
        "derived from trusted caller context."
    ),
    responses=ADVISOR_COCKPIT_ACKNOWLEDGEMENT_RESPONSES,
)
async def acknowledge_advisor_cockpit_action(
    caller: AdvisorCockpitCaller,
    request: AdvisorCockpitAcknowledgeRequest,
    action_item_id: str = Path(
        ...,
        description="Advisor cockpit action item identifier owned by lotus-advise.",
        examples=["cockpit_action_policy_review_required_001"],
    ),
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Required idempotency key for replay-safe cockpit acknowledgements.",
        examples=["idem-cockpit-ack-001"],
    ),
    portfolio_id: str = Query(
        ...,
        description="Entitled portfolio identifier used for object-level action authorization.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
) -> AdvisorCockpitEnvelopeResponse:
    return await _acknowledge_advisor_cockpit_action(
        caller=caller,
        request=request,
        action_item_id=action_item_id,
        idempotency_key=idempotency_key,
        portfolio_id=portfolio_id,
    )
