from typing import Any

from fastapi import APIRouter, Header, Path, Query, status

from app.contracts.advisor_cockpit import (
    AdvisorCockpitAcknowledgeRequest,
    AdvisorCockpitEnvelopeResponse,
    AdvisorCockpitHouseViewCohortRequest,
    AdvisorCockpitOwnerRole,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisor_cockpit_service import AdvisorCockpitService
from app.services.advisory_service_factory import build_advisor_cockpit_service

router = APIRouter(prefix="/api/v1/advisor-cockpit", tags=["advisor-cockpit"])

ADVISOR_COCKPIT_READ_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "description": "Advisor cockpit action item was not found by lotus-advise."
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "description": "lotus-advise rejected the cockpit request validation context."
    },
}
ADVISOR_COCKPIT_ACKNOWLEDGEMENT_RESPONSES: dict[int | str, dict[str, Any]] = {
    **ADVISOR_COCKPIT_READ_RESPONSES,
    status.HTTP_409_CONFLICT: {
        "description": "lotus-advise rejected a conflicting acknowledgement idempotency key."
    },
}


def _advisor_cockpit_service() -> AdvisorCockpitService:
    return build_advisor_cockpit_service()


def _cockpit_params(
    *,
    portfolio_id: str | None,
    advisor_id: str | None,
    role: AdvisorCockpitOwnerRole,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "advisor_id": advisor_id,
        "role": role,
        "limit": limit,
        "cursor": cursor,
    }
    return {key: value for key, value in params.items() if value is not None}


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
    return await _advisor_cockpit_service().list_actions(
        params=_cockpit_params(
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
    return await _advisor_cockpit_service().list_preparation_packets(
        params=_cockpit_params(
            portfolio_id=portfolio_id,
            advisor_id=advisor_id,
            role=role,
            limit=limit,
            cursor=cursor,
        ),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/actions/{action_item_id}",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="Get Advisor Cockpit Action",
    description=(
        "Returns one source-owned advisor cockpit action item from lotus-advise. Gateway does "
        "not infer policy, memo, supportability, SLA, acknowledgement, or owner-role posture."
    ),
    responses=ADVISOR_COCKPIT_READ_RESPONSES,
)
async def get_advisor_cockpit_action(
    action_item_id: str = Path(
        ...,
        description="Advisor cockpit action item identifier owned by lotus-advise.",
        examples=["cockpit_action_policy_review_required_001"],
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
    return await _advisor_cockpit_service().get_action(
        action_item_id=action_item_id,
        params=_cockpit_params(portfolio_id=portfolio_id, advisor_id=advisor_id, role=role),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/snapshot",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="Get Advisor Cockpit Snapshot",
    description=(
        "Returns the source-owned advisor cockpit operating snapshot from lotus-advise. Gateway "
        "preserves supportability, blocked client-ready posture, and unsupported capability "
        "boundaries without local aggregation."
    ),
    responses=ADVISOR_COCKPIT_READ_RESPONSES,
)
async def get_advisor_cockpit_snapshot(
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
    return await _advisor_cockpit_service().get_snapshot(
        params=_cockpit_params(portfolio_id=portfolio_id, advisor_id=advisor_id, role=role),
        correlation_id=correlation_id_var.get(),
    )


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
    return await _advisor_cockpit_service().get_supportability(
        params=_cockpit_params(portfolio_id=portfolio_id, advisor_id=advisor_id, role=role),
        correlation_id=correlation_id_var.get(),
    )


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
    return await _advisor_cockpit_service().acknowledge_action(
        action_item_id=action_item_id,
        body=request.model_dump(exclude_none=True),
        params=_cockpit_params(portfolio_id=portfolio_id, advisor_id=advisor_id, role=role),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/house-view-cohorts/evaluate",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="Evaluate Advisor Cockpit House-View Cohort",
    description=(
        "Forwards a source-backed tactical house-view affected-cohort request to lotus-advise so "
        "subsequent advisor cockpit reads can surface DPM-owned `HOUSE_VIEW_IMPACT_REVIEW` "
        "actions. Gateway preserves the Advise cohort product and does not discover candidate "
        "portfolios, infer DPM eligibility, create campaigns, approve trades, or claim OMS "
        "execution."
    ),
)
async def evaluate_advisor_cockpit_house_view_cohort(
    request: AdvisorCockpitHouseViewCohortRequest,
) -> AdvisorCockpitEnvelopeResponse:
    return await _advisor_cockpit_service().evaluate_house_view_cohort(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
