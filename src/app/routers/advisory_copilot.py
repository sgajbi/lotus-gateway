from typing import Any

from fastapi import APIRouter, Body, Header, Path, Query

from app.contracts.advisory_copilot import AdvisoryCopilotEnvelopeResponse
from app.routers.correlation import resolve_router_correlation_id
from app.services.advisory_service_provider import advisory_copilot_service

router = APIRouter(prefix="/api/v1/advisory-copilot", tags=["advisory-copilot"])


def _correlation_id(x_correlation_id: str | None) -> str:
    return resolve_router_correlation_id(x_correlation_id)


@router.post(
    "/evidence-packets",
    response_model=AdvisoryCopilotEnvelopeResponse,
    status_code=201,
    summary="Create Advisory Copilot Evidence Packet",
    description=(
        "Forwards a bounded advisory copilot evidence-packet request to lotus-advise. Gateway "
        "does not select evidence, redact source data, generate copilot output, or reinterpret "
        "client-ready publication boundaries."
    ),
)
async def create_advisory_copilot_evidence_packet(
    body: dict[str, Any] = Body(...),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> AdvisoryCopilotEnvelopeResponse:
    return await advisory_copilot_service().create_evidence_packet(
        body=body,
        correlation_id=_correlation_id(x_correlation_id),
    )


@router.post(
    "/evidence-packets/from-proposal-version",
    response_model=AdvisoryCopilotEnvelopeResponse,
    status_code=201,
    summary="Create Proposal Version Advisory Copilot Evidence Packet",
    description=(
        "Forwards proposal-version evidence packet projection to lotus-advise so Advise remains "
        "the source of proposal, memo, policy, cockpit, report-readiness, handoff, redaction, "
        "hash, and lineage truth."
    ),
)
async def create_advisory_copilot_evidence_packet_from_proposal_version(
    body: dict[str, Any] = Body(...),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> AdvisoryCopilotEnvelopeResponse:
    return await advisory_copilot_service().create_evidence_packet_from_proposal_version(
        body=body,
        correlation_id=_correlation_id(x_correlation_id),
    )


@router.get(
    "/evidence-packets/{evidence_packet_id}",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="Get Advisory Copilot Evidence Packet",
    description=(
        "Returns a persisted Advise-owned advisory copilot evidence packet without Gateway-side "
        "evidence reconstruction."
    ),
)
async def get_advisory_copilot_evidence_packet(
    evidence_packet_id: str = Path(
        description="Advisory copilot evidence-packet identifier owned by lotus-advise."
    ),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> AdvisoryCopilotEnvelopeResponse:
    return await advisory_copilot_service().get_evidence_packet(
        evidence_packet_id=evidence_packet_id,
        correlation_id=_correlation_id(x_correlation_id),
    )


@router.post(
    "/actions",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="Run Governed Advisory Copilot Action",
    description=(
        "Forwards a governed copilot action request to lotus-advise. Gateway preserves run, "
        "guardrail, workflow-pack, hash, lineage, and review posture and does not execute AI "
        "workflow packs locally."
    ),
)
async def run_advisory_copilot_action(
    body: dict[str, Any] = Body(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> AdvisoryCopilotEnvelopeResponse:
    return await advisory_copilot_service().run_action(
        body=body,
        idempotency_key=idempotency_key,
        correlation_id=_correlation_id(x_correlation_id),
    )


@router.get(
    "/actions/{run_id}",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="Get Advisory Copilot Run",
    description=(
        "Returns an Advise-owned advisory copilot run with review audit events without "
        "Gateway-side run reconstruction."
    ),
)
async def get_advisory_copilot_run(
    run_id: str = Path(description="Advisory copilot run identifier owned by lotus-advise."),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> AdvisoryCopilotEnvelopeResponse:
    return await advisory_copilot_service().get_run(
        run_id=run_id,
        correlation_id=_correlation_id(x_correlation_id),
    )


@router.post(
    "/actions/{run_id}/reviews",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="Review Advisory Copilot Run",
    description=(
        "Forwards an idempotent human review action to lotus-advise. Review approval remains "
        "internal-use posture only and does not approve proposals, policy outcomes, orders, "
        "reports, or client-ready communication."
    ),
)
async def review_advisory_copilot_run(
    body: dict[str, Any] = Body(...),
    run_id: str = Path(description="Advisory copilot run identifier owned by lotus-advise."),
    idempotency_key: str = Header(alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> AdvisoryCopilotEnvelopeResponse:
    return await advisory_copilot_service().review_run(
        run_id=run_id,
        body=body,
        idempotency_key=idempotency_key,
        correlation_id=_correlation_id(x_correlation_id),
    )


@router.get(
    "/supportability",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="Get Advisory Copilot Supportability",
    description=(
        "Returns Advise-owned advisory copilot supportability and unsupported claim boundaries. "
        "Gateway does not infer demo readiness or client-ready publication."
    ),
)
async def get_advisory_copilot_supportability(
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> AdvisoryCopilotEnvelopeResponse:
    return await advisory_copilot_service().get_supportability(
        correlation_id=_correlation_id(x_correlation_id),
    )


@router.get(
    "/proposals/{proposal_id}/versions/{version_id}/runs",
    response_model=AdvisoryCopilotEnvelopeResponse,
    summary="List Proposal Version Advisory Copilot Runs",
    description=(
        "Lists Advise-owned advisory copilot runs for a proposal version. Gateway forwards "
        "pagination only and does not rebuild copilot lineage."
    ),
)
async def list_advisory_copilot_proposal_version_runs(
    proposal_id: str = Path(description="Proposal identifier owned by lotus-advise."),
    version_id: str = Path(description="Proposal version identifier owned by lotus-advise."),
    limit: int = Query(default=25, ge=1, le=100),
    cursor: str | None = Query(default=None),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> AdvisoryCopilotEnvelopeResponse:
    return await advisory_copilot_service().list_proposal_version_runs(
        proposal_id=proposal_id,
        version_id=version_id,
        params={"limit": limit, "cursor": cursor},
        correlation_id=_correlation_id(x_correlation_id),
    )
