from fastapi import APIRouter, Header, Path, status

from app.clients.advise_client import AdviseClient
from app.config import settings
from app.contracts.advisory_copilot import (
    AdvisoryCopilotBodyRequest,
    AdvisoryCopilotEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_copilot_service import AdvisoryCopilotService

router = APIRouter(prefix="/api/v1/advisory-copilot", tags=["advisory-copilot"])

ADVISORY_COPILOT_RESPONSES: dict[int | str, dict[str, str]] = {
    status.HTTP_404_NOT_FOUND: {"description": "lotus-advise could not find the copilot record."},
    status.HTTP_409_CONFLICT: {
        "description": "lotus-advise rejected a conflicting idempotency or review request."
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": "lotus-advise rejected the copilot request validation context."
    },
}


def _advisory_copilot_service() -> AdvisoryCopilotService:
    return AdvisoryCopilotService(
        advise_client=AdviseClient(
            base_url=settings.decisioning_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        )
    )


@router.post(
    "/evidence-packets",
    response_model=AdvisoryCopilotEnvelopeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Advisory Copilot Evidence Packet",
    description=(
        "Forwards bounded evidence-packet creation to lotus-advise. Gateway preserves the "
        "Advise-owned evidence packet and does not reconstruct evidence or prompt context."
    ),
    responses=ADVISORY_COPILOT_RESPONSES,
)
async def create_advisory_copilot_evidence_packet(
    request: AdvisoryCopilotBodyRequest,
) -> AdvisoryCopilotEnvelopeResponse:
    return await _advisory_copilot_service().create_evidence_packet(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/evidence-packets/from-proposal-version",
    response_model=AdvisoryCopilotEnvelopeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Proposal Version Advisory Copilot Evidence Packet",
    description=(
        "Forwards source-owned proposal-version evidence projection to lotus-advise. Workbench "
        "and other clients request proposal/version/action-family scope; Gateway does not "
        "construct evidence sections, prompts, guardrails, review state, or advisory semantics."
    ),
    responses=ADVISORY_COPILOT_RESPONSES,
)
async def create_advisory_copilot_evidence_packet_from_proposal_version(
    request: AdvisoryCopilotBodyRequest,
) -> AdvisoryCopilotEnvelopeResponse:
    return await _advisory_copilot_service().create_evidence_packet_from_proposal_version(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/evidence-packets/{evidence_packet_id}",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="Get Advisory Copilot Evidence Packet",
    description="Returns an Advise-owned copilot evidence packet through the Gateway contract.",
    responses=ADVISORY_COPILOT_RESPONSES,
)
async def get_advisory_copilot_evidence_packet(
    evidence_packet_id: str = Path(
        ...,
        description="Advise-owned copilot evidence-packet identifier.",
        examples=["copilot_packet_pb_sg_001"],
    ),
) -> AdvisoryCopilotEnvelopeResponse:
    return await _advisory_copilot_service().get_evidence_packet(
        evidence_packet_id=evidence_packet_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/actions",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="Run Advisory Copilot Action",
    description=(
        "Runs an Advise-owned governed advisory copilot action from a persisted evidence packet. "
        "Gateway forwards idempotency and correlation context without calling lotus-ai directly."
    ),
    responses=ADVISORY_COPILOT_RESPONSES,
)
async def run_advisory_copilot_action(
    request: AdvisoryCopilotBodyRequest,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional replay-safe copilot action idempotency key.",
        examples=["copilot-action-idem-001"],
    ),
) -> AdvisoryCopilotEnvelopeResponse:
    return await _advisory_copilot_service().run_action(
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/actions/{run_id}",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="Get Advisory Copilot Run",
    description="Returns an Advise-owned copilot run and review audit events.",
    responses=ADVISORY_COPILOT_RESPONSES,
)
async def get_advisory_copilot_run(
    run_id: str = Path(
        ...,
        description="Advise-owned advisory copilot run identifier.",
        examples=["copilot_run_001"],
    ),
) -> AdvisoryCopilotEnvelopeResponse:
    return await _advisory_copilot_service().get_run(
        run_id=run_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/actions/{run_id}/reviews",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="Review Advisory Copilot Run",
    description=(
        "Records a review action through lotus-advise. Gateway does not approve proposal "
        "lifecycle, policy, report, order, or client-ready publication state."
    ),
    responses=ADVISORY_COPILOT_RESPONSES,
)
async def review_advisory_copilot_run(
    request: AdvisoryCopilotBodyRequest,
    run_id: str = Path(..., description="Advise-owned advisory copilot run identifier."),
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Required replay-safe review idempotency key.",
        examples=["copilot-review-idem-001"],
    ),
) -> AdvisoryCopilotEnvelopeResponse:
    return await _advisory_copilot_service().review_run(
        run_id=run_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/supportability",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="Get Advisory Copilot Supportability",
    description="Returns Advise-owned advisory copilot supportability and unsupported boundaries.",
    responses=ADVISORY_COPILOT_RESPONSES,
)
async def get_advisory_copilot_supportability() -> AdvisoryCopilotEnvelopeResponse:
    return await _advisory_copilot_service().get_supportability(
        correlation_id=correlation_id_var.get()
    )


@router.get(
    "/proposals/{proposal_id}/versions/{version_id}/runs",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="List Proposal Version Advisory Copilot Runs",
    description="Lists Advise-owned copilot runs for a proposal version scope.",
    responses=ADVISORY_COPILOT_RESPONSES,
)
async def list_proposal_version_advisory_copilot_runs(
    proposal_id: str = Path(..., description="Advise-owned proposal identifier."),
    version_id: str = Path(..., description="Advise-owned proposal version identifier."),
) -> AdvisoryCopilotEnvelopeResponse:
    return await _advisory_copilot_service().list_proposal_version_runs(
        proposal_id=proposal_id,
        version_id=version_id,
        correlation_id=correlation_id_var.get(),
    )
