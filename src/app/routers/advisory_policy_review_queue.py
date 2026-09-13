from fastapi import APIRouter, Query

from app.contracts.advisory_policy import AdvisoryPolicyEnvelopeResponse
from app.routers.advisory_policy_common import (
    CALLER_CONTEXT_RESPONSES,
    AdmittedCallerHeaders,
    AdvisoryPolicyRouteResponse,
    admitted_policy_read,
)
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _get_policy_review_queue(
    *,
    evaluation_status: str | None,
    portfolio_id: str | None,
    caller_headers: AdmittedCallerHeaders,
) -> AdvisoryPolicyRouteResponse:
    return await admitted_policy_read(
        caller_headers=caller_headers,
        call=lambda caller, correlation_id: advisory_policy_service().get_policy_review_queue(
            evaluation_status=evaluation_status,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            caller=caller,
        ),
    )


@router.get(
    "/advisory-policy-evaluations/review-queue",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="List Advisory Policy Review Queue",
    description=(
        "Returns tenant-scoped policy evaluation review-queue items from lotus-advise for "
        "admitted advisor, compliance, and policy-checker callers."
    ),
    responses=CALLER_CONTEXT_RESPONSES,
)
async def get_policy_review_queue(
    caller_headers: AdmittedCallerHeaders,
    evaluation_status: str | None = Query(
        default=None,
        description="Optional policy evaluation status filter owned by lotus-advise.",
        examples=["PENDING_REVIEW"],
    ),
    portfolio_id: str | None = Query(
        default=None,
        description="Optional portfolio identifier filter owned by lotus-advise.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
) -> AdvisoryPolicyRouteResponse:
    return await _get_policy_review_queue(
        evaluation_status=evaluation_status,
        portfolio_id=portfolio_id,
        caller_headers=caller_headers,
    )
