from fastapi import APIRouter, Header

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_policy_evaluation_common import POLICY_EVALUATION_PATH
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


@router.post(
    "/advisory-policy-evaluations/{evaluation_id}/report-packages",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Request Advisory Policy Report Package",
    description=(
        "Requests a source-owned advisor/compliance policy sign-off package through lotus-advise. "
        "Gateway does not promote blocked or degraded evaluations to client-ready publication."
    ),
)
async def request_policy_report_package(
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str = POLICY_EVALUATION_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for policy report packages.",
        examples=["idem-policy-report-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().request_policy_report_package(
        evaluation_id=evaluation_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )
