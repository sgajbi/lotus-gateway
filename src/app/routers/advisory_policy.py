from fastapi import APIRouter, Header, Path, Query

from app.clients.advise_client import AdviseClient
from app.config import settings
from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_policy_service import AdvisoryPolicyService

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])
POLICY_VERSION_PATH = Path(
    ...,
    description="Policy pack version identifier owned by lotus-advise.",
)
POLICY_EVALUATION_PATH = Path(
    ...,
    description="Policy evaluation identifier owned by lotus-advise.",
)


def _advisory_policy_service() -> AdvisoryPolicyService:
    return AdvisoryPolicyService(
        advise_client=AdviseClient(
            base_url=settings.decisioning_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        )
    )


@router.get(
    "/advisory-policy-packs",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="List Advisory Policy Packs",
    description=(
        "Returns enterprise suitability and best-interest policy packs from lotus-advise. "
        "Gateway does not assemble or validate policy facts locally."
    ),
)
async def list_policy_packs() -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().list_policy_packs(
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/advisory-policy-packs/{policy_pack_id}/versions/{policy_version}",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Pack Version",
    description=(
        "Returns a source-owned policy pack version from lotus-advise, including its "
        "supportability and activation posture when supplied by Advise."
    ),
)
async def get_policy_pack_version(
    policy_pack_id: str = Path(
        ...,
        description="Policy pack identifier owned by lotus-advise.",
        examples=["policy_pack_sg_private_banking"],
    ),
    policy_version: str = Path(
        ...,
        description="Policy pack version identifier owned by lotus-advise.",
        examples=["2026.05"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().get_policy_pack_version(
        policy_pack_id=policy_pack_id,
        policy_version=policy_version,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/advisory-policy-packs/{policy_pack_id}/versions/{policy_version}/validate",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Validate Advisory Policy Pack Version",
    description=(
        "Requests source-owned policy pack validation through lotus-advise. Gateway forwards "
        "the request body and idempotency key without recomputing rule readiness."
    ),
)
async def validate_policy_pack_version(
    request: AdvisoryPolicyBodyRequest,
    policy_pack_id: str = Path(..., description="Policy pack identifier owned by lotus-advise."),
    policy_version: str = POLICY_VERSION_PATH,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Required idempotency key for policy validation.",
        examples=["idem-policy-validate-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().validate_policy_pack_version(
        policy_pack_id=policy_pack_id,
        policy_version=policy_version,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/advisory-policy-packs/{policy_pack_id}/versions/{policy_version}/activate",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Activate Advisory Policy Pack Version",
    description=(
        "Requests policy pack activation through lotus-advise. Activation posture remains "
        "owned by Advise and is returned unchanged by Gateway."
    ),
)
async def activate_policy_pack_version(
    request: AdvisoryPolicyBodyRequest,
    policy_pack_id: str = Path(..., description="Policy pack identifier owned by lotus-advise."),
    policy_version: str = POLICY_VERSION_PATH,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Required idempotency key for policy activation.",
        examples=["idem-policy-activate-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().activate_policy_pack_version(
        policy_pack_id=policy_pack_id,
        policy_version=policy_version,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/proposals/{proposal_id}/versions/{proposal_version_id}/policy-evaluations",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Create Advisory Policy Evaluation",
    description=(
        "Creates a source-owned suitability and best-interest policy evaluation through "
        "lotus-advise. Gateway does not infer suitability, supportability, sign-off, or "
        "client-ready readiness locally."
    ),
)
async def create_policy_evaluation(
    request: AdvisoryPolicyBodyRequest,
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
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().create_policy_evaluation(
        proposal_id=proposal_id,
        proposal_version_id=proposal_version_id,
        body=request.body,
        idempotency_key=idempotency_key,
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
    return await _advisory_policy_service().get_policy_review_queue(
        evaluation_status=evaluation_status,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/advisory-policy-evaluations/{evaluation_id}",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Evaluation",
    description="Returns a source-owned policy evaluation from lotus-advise.",
)
async def get_policy_evaluation(
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().get_policy_evaluation(
        evaluation_id=evaluation_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/advisory-policy-evaluations/{evaluation_id}/replay",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Replay Advisory Policy Evaluation",
    description=(
        "Requests policy evaluation replay through lotus-advise and preserves replay evidence "
        "unchanged for support and supervisory review."
    ),
)
async def replay_policy_evaluation(
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().replay_policy_evaluation(
        evaluation_id=evaluation_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/advisory-policy-evaluations/{evaluation_id}/events",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Record Advisory Policy Evaluation Event",
    description=(
        "Records a source-owned policy evaluation event through lotus-advise. Gateway does "
        "not mutate lifecycle state locally."
    ),
)
async def record_policy_evaluation_event(
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str = POLICY_EVALUATION_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for policy evaluation events.",
        examples=["idem-policy-event-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().record_policy_evaluation_event(
        evaluation_id=evaluation_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/advisory-policy-evaluations/{evaluation_id}/lineage",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Evaluation Lineage",
    description="Returns source lineage for a policy evaluation from lotus-advise.",
)
async def get_policy_evaluation_lineage(
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().get_policy_evaluation_lineage(
        evaluation_id=evaluation_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/advisory-policy-evaluations/{evaluation_id}/sign-off-package",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Sign-off Package",
    description=(
        "Returns the source-owned sign-off package from lotus-advise, including "
        "maker-checker and client-ready blockers when supplied by Advise."
    ),
)
async def get_policy_sign_off_package(
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().get_policy_sign_off_package(
        evaluation_id=evaluation_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/advisory-policy-evaluations/{evaluation_id}/workflow",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Workflow",
    description="Returns policy workflow posture from lotus-advise without Gateway-side inference.",
)
async def get_policy_evaluation_workflow(
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().get_policy_evaluation_workflow(
        evaluation_id=evaluation_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/advisory-policy-evaluations/{evaluation_id}/sign-off-decisions",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Record Advisory Policy Sign-off Decision",
    description=(
        "Records maker-checker or supervisory sign-off decisions through lotus-advise. "
        "Gateway forwards the decision and returns Advise's resulting posture unchanged."
    ),
)
async def record_policy_sign_off_decision(
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str = POLICY_EVALUATION_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for sign-off decisions.",
        examples=["idem-policy-signoff-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().record_policy_sign_off_decision(
        evaluation_id=evaluation_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


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
    return await _advisory_policy_service().request_policy_report_package(
        evaluation_id=evaluation_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/advisory-policy-evaluations/{evaluation_id}/ai-evidence",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Request Advisory Policy AI Evidence",
    description=(
        "Requests bounded policy evidence through lotus-advise. AI output remains "
        "non-authoritative; Advise owns redaction, fail-closed posture, and client-ready blockers."
    ),
)
async def request_policy_ai_evidence(
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str = POLICY_EVALUATION_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for policy AI evidence requests.",
        examples=["idem-policy-ai-evidence-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await _advisory_policy_service().request_policy_ai_evidence(
        evaluation_id=evaluation_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )
