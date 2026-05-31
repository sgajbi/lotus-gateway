from fastapi import APIRouter, Query

from app.contracts.advisory_policy import AdvisoryPolicyEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _get_policy_review_queue(
    *,
    evaluation_status: str | None,
    portfolio_id: str | None,
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().get_policy_review_queue(
        evaluation_status=evaluation_status,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/advisory-policy-evaluations/review-queue",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="List Advisory Policy Review Queue",
    description=(
        "Returns policy evaluation review-queue items from lotus-advise for advisor, "
        "compliance, investment desk, operations, and supervisory workflows."
    ),
)
async def get_policy_review_queue(
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
) -> AdvisoryPolicyEnvelopeResponse:
    return await _get_policy_review_queue(
        evaluation_status=evaluation_status,
        portfolio_id=portfolio_id,
    )
