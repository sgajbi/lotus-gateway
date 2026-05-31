from fastapi import APIRouter, Header, Path, Query

from app.contracts.advisor_cockpit import (
    AdvisorCockpitAcknowledgeRequest,
    AdvisorCockpitEnvelopeResponse,
    AdvisorCockpitOwnerRole,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisor_cockpit_common import (
    ADVISOR_COCKPIT_ACKNOWLEDGEMENT_RESPONSES,
    cockpit_params,
)
from app.services.advisory_service_provider import advisor_cockpit_service

router = APIRouter(prefix="/api/v1/advisor-cockpit", tags=["advisor-cockpit"])


@router.post(
    "/actions/{action_item_id}/acknowledgements",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="Acknowledge Advisor Cockpit Action",
    description=(
        "Records an idempotent acknowledgement through lotus-advise. Gateway forwards the "
        "observed action version and idempotency key, and does not clear blocking policy, memo, "
        "supportability, owner-role, or client-ready posture locally."
    ),
    responses=ADVISOR_COCKPIT_ACKNOWLEDGEMENT_RESPONSES,
)
async def acknowledge_advisor_cockpit_action(
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
    return await advisor_cockpit_service().acknowledge_action(
        action_item_id=action_item_id,
        body=request.model_dump(exclude_none=True),
        params=cockpit_params(portfolio_id=portfolio_id, advisor_id=advisor_id, role=role),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )
