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
    "/actions",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="List Advisor Cockpit Actions",
    description=(
        "Lists source-owned advisor cockpit action items from lotus-advise. Gateway preserves "
        "Advise-owned action status, priority, owner role, reason codes, evidence refs, lineage "
        "refs, and unsupported-capability posture without reconstructing advisory semantics."
    ),
    responses=ADVISOR_COCKPIT_READ_RESPONSES,
)
async def list_advisor_cockpit_actions(
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
    limit: int = Query(
        default=25,
        ge=1,
        le=100,
        description="Bounded cockpit action page size forwarded to lotus-advise.",
        examples=[25],
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque action cursor returned by lotus-advise.",
        examples=["cockpit_action_001"],
    ),
) -> AdvisorCockpitEnvelopeResponse:
    return await advisor_cockpit_service().list_actions(
        params=cockpit_params(
            portfolio_id=portfolio_id,
            advisor_id=advisor_id,
            role=role,
            limit=limit,
            cursor=cursor,
        ),
        correlation_id=correlation_id_var.get(),
    )
