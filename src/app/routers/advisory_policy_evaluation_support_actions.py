from typing import Annotated

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_policy_common import (
    CALLER_CONTEXT_RESPONSES,
    AdvisoryPolicyCallerHeaders,
    admit_advisory_policy_caller,
    advisory_policy_caller_headers,
    advisory_policy_error_response,
)
from app.routers.advisory_policy_evaluation_common import POLICY_EVALUATION_PATH
from app.services.advisory_policy_access_policy import (
    POLICY_EVALUATION_REPORT_PACKAGE,
    AdvisoryPolicyCallerContextError,
)
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _request_policy_report_package(
    *,
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str,
    idempotency_key: str | None,
    caller_headers: AdvisoryPolicyCallerHeaders,
) -> AdvisoryPolicyEnvelopeResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    try:
        caller = admit_advisory_policy_caller(
            operation=POLICY_EVALUATION_REPORT_PACKAGE,
            caller_headers=caller_headers,
        )
    except AdvisoryPolicyCallerContextError as exc:
        return advisory_policy_error_response(error=exc, correlation_id=correlation_id)
    return await advisory_policy_service().request_policy_report_package(
        evaluation_id=evaluation_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        caller=caller,
    )


@router.post(
    "/advisory-policy-evaluations/{evaluation_id}/report-packages",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Request Advisory Policy Report Package",
    description=(
        "Requests a source-owned advisor/compliance policy sign-off package through lotus-advise. "
        "Gateway does not promote blocked or degraded evaluations to client-ready publication."
    ),
    responses=CALLER_CONTEXT_RESPONSES,
)
async def request_policy_report_package(
    request: AdvisoryPolicyBodyRequest,
    caller_headers: Annotated[AdvisoryPolicyCallerHeaders, Depends(advisory_policy_caller_headers)],
    evaluation_id: str = POLICY_EVALUATION_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for policy report packages.",
        examples=["idem-policy-report-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse | JSONResponse:
    return await _request_policy_report_package(
        request=request,
        evaluation_id=evaluation_id,
        idempotency_key=idempotency_key,
        caller_headers=caller_headers,
    )
