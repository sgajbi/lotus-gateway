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


async def _list_advisor_cockpit_preparation_packets(
    *,
    portfolio_id: str | None,
    advisor_id: str | None,
    role: AdvisorCockpitOwnerRole,
    limit: int,
    cursor: str | None,
) -> AdvisorCockpitEnvelopeResponse:
    return await advisor_cockpit_service().list_preparation_packets(
        params=cockpit_params(
            portfolio_id=portfolio_id,
            advisor_id=advisor_id,
            role=role,
            limit=limit,
            cursor=cursor,
        ),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/preparation-packets",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="List Advisor Cockpit Preparation Packets",
    description=(
        "Lists source-owned advisor cockpit preparation packets from lotus-advise. Gateway "
        "preserves meeting agenda, proposal context, memo evidence, policy posture, follow-up "
        "posture, lineage refs, and supportability exactly as supplied by Advise without "
        "reconstructing preparation semantics."
    ),
    responses=ADVISOR_COCKPIT_READ_RESPONSES,
)
async def list_advisor_cockpit_preparation_packets(
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
        description="Bounded preparation packet page size forwarded to lotus-advise.",
        examples=[25],
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque preparation packet cursor returned by lotus-advise.",
        examples=["prep_packet_001"],
    ),
) -> AdvisorCockpitEnvelopeResponse:
    return await _list_advisor_cockpit_preparation_packets(
        portfolio_id=portfolio_id,
        advisor_id=advisor_id,
        role=role,
        limit=limit,
        cursor=cursor,
    )
