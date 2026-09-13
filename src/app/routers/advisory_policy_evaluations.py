from collections.abc import Mapping

from fastapi import APIRouter, Depends, Header, Path

from app.contracts.advisory_policy import (
    AdvisoryPolicyEnvelopeResponse,
    AdvisoryPolicyEvaluationFinalizeRequest,
)
from app.routers.advisory_policy_common import (
    CALLER_CONTEXT_RESPONSES,
    AdmittedCallerHeaders,
    AdvisoryPolicyRouteResponse,
    admitted_policy_write,
    required_policy_evaluation_scope_headers,
)
from app.services.advisory_policy_access_policy import (
    POLICY_EVALUATION_FINALIZE,
    AdvisoryPolicyCallerContext,
    AdvisoryPolicyCallerContextError,
)
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


def _require_finalize_request_scope(
    *, caller: AdvisoryPolicyCallerContext, proposal_id: str, body: Mapping[str, object]
) -> None:
    """Refuse business identifiers outside the caller's already-admitted scope."""
    evidence = body.get("evidence_bundle")
    inputs = evidence.get("inputs") if isinstance(evidence, Mapping) else None
    snapshot = inputs.get("portfolio_snapshot") if isinstance(inputs, Mapping) else None
    portfolio_id = (
        str(snapshot.get("portfolio_id") or "").strip() if isinstance(snapshot, Mapping) else None
    )
    if (
        caller.authorized_proposal_id != proposal_id
        or not portfolio_id
        or caller.authorized_portfolio_id != portfolio_id
    ):
        raise AdvisoryPolicyCallerContextError(
            code="advisory_policy_evaluation_scope_denied",
            message="Advisory-policy evaluation scope does not cover this request.",
            status_code=403,
        )


async def _create_policy_evaluation(
    *,
    request: AdvisoryPolicyEvaluationFinalizeRequest,
    proposal_id: str,
    proposal_version_id: str,
    idempotency_key: str,
    caller_headers: AdmittedCallerHeaders,
) -> AdvisoryPolicyRouteResponse:
    body = request.body.model_dump(mode="json")
    return await admitted_policy_write(
        operation=POLICY_EVALUATION_FINALIZE,
        caller_headers=caller_headers,
        request_scope_validator=lambda caller: _require_finalize_request_scope(
            caller=caller,
            proposal_id=proposal_id,
            body=body,
        ),
        call=lambda caller, correlation_id: advisory_policy_service().create_policy_evaluation(
            proposal_id=proposal_id,
            proposal_version_id=proposal_version_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            caller=caller,
        ),
    )


@router.post(
    "/proposals/{proposal_id}/versions/{proposal_version_id}/policy-evaluations",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Create Advisory Policy Evaluation",
    description=(
        "Creates a source-owned suitability and best-interest policy evaluation through "
        "lotus-advise. Gateway does not infer suitability, supportability, sign-off, or "
        "client-ready readiness locally. The evaluation executes under the caller's own "
        "admitted tenant, legal entity and actor identity; Gateway forwards that scope "
        "unchanged and does not substitute one of its own."
    ),
    responses=CALLER_CONTEXT_RESPONSES,
    dependencies=[Depends(required_policy_evaluation_scope_headers)],
)
async def create_policy_evaluation(
    request: AdvisoryPolicyEvaluationFinalizeRequest,
    caller_headers: AdmittedCallerHeaders,
    proposal_id: str = Path(..., description="Proposal identifier owned by lotus-advise."),
    proposal_version_id: str = Path(
        ...,
        description="Proposal version identifier owned by lotus-advise.",
    ),
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Required idempotency key for policy evaluation creation.",
        examples=["idem-policy-evaluation-1"],
    ),
) -> AdvisoryPolicyRouteResponse:
    return await _create_policy_evaluation(
        request=request,
        proposal_id=proposal_id,
        proposal_version_id=proposal_version_id,
        idempotency_key=idempotency_key,
        caller_headers=caller_headers,
    )
