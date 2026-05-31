from fastapi import APIRouter, Path

from app.contracts.dpm_proof_packs import (
    DpmProofPackErrorDetail,
    DpmProofPackGatewayResponse,
    DpmProofPackGenerateRequest,
    DpmProofPackMarkdownResponse,
    DpmProofPackMemoGatewayResponse,
    DpmProofPackMemoRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.services.dpm_service_provider import dpm_proof_pack_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/proof-packs",
    tags=["DPM Command Center"],
)
_UPSTREAM_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmProofPackErrorDetail,
    not_found_description="lotus-manage could not find the requested proof pack or source.",
    conflict_description="lotus-manage rejected the proof-pack request as conflicting.",
    invalid_payload_description="lotus-manage rejected the proof-pack payload as invalid.",
    unavailable_description="lotus-manage proof-pack authority is unavailable or degraded.",
)


@router.post(
    "",
    response_model=DpmProofPackGatewayResponse,
    summary="Generate DPM proof pack",
    description=(
        "What: asks lotus-manage to generate an immutable RFC-0040 DPM proof pack from a "
        "rebalance run or selected construction alternative. When: call this after manage source "
        "readiness indicates proof evidence can be assembled for PM, compliance, or operations "
        "review. How: Gateway forwards the body and idempotency key to manage, then preserves the "
        "returned proof_pack_id, section states, reason codes, hashes, source refs, report refs, "
        "and AI refs without rebuilding proof-pack evidence."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def generate_proof_pack(
    request: DpmProofPackGenerateRequest,
) -> DpmProofPackGatewayResponse:
    return await dpm_proof_pack_service().generate_proof_pack(
        body=request.body,
        idempotency_key=request.idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{proof_pack_id}",
    response_model=DpmProofPackGatewayResponse,
    summary="Get DPM proof pack",
    description=(
        "What: returns one manage-owned RFC-0040 proof pack for Workbench evidence drawers and "
        "audit review. When: call this after a rebalance run or wave item links to a "
        "proof_pack_id. How: Gateway retrieves the manage payload by id and preserves proof-pack "
        "identity, "
        "section states, reason codes, hashes, source lineage, report refs, and AI refs without "
        "recalculation."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_proof_pack(
    proof_pack_id: str = Path(
        ...,
        description="Manage-owned immutable proof-pack identifier.",
        examples=["dpp_rr_001"],
    ),
) -> DpmProofPackGatewayResponse:
    return await dpm_proof_pack_service().get_proof_pack(
        proof_pack_id=proof_pack_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{proof_pack_id}/summary.md",
    response_model=DpmProofPackMarkdownResponse,
    summary="Get DPM proof-pack Markdown",
    description=(
        "What: returns manage-rendered deterministic Markdown for one RFC-0040 proof pack. "
        "When: call this for human-readable PM, compliance, operations, or audit review. How: "
        "Gateway preserves the manage Markdown text in an envelope for Workbench and does not "
        "summarize, render, or regenerate proof-pack content."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_proof_pack_markdown(
    proof_pack_id: str = Path(
        ...,
        description="Manage-owned immutable proof-pack identifier.",
        examples=["dpp_rr_001"],
    ),
) -> DpmProofPackMarkdownResponse:
    return await dpm_proof_pack_service().get_proof_pack_markdown(
        proof_pack_id=proof_pack_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{proof_pack_id}/report-input",
    response_model=DpmProofPackGatewayResponse,
    summary="Get DPM proof-pack report input",
    description=(
        "What: returns manage-owned deterministic report-input evidence for one RFC-0040 proof "
        "pack. When: call this before requesting report materialization from lotus-report. How: "
        "Gateway preserves the report-input payload and exposes only experience-layer posture; "
        "lotus-report remains the report materialization authority."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_proof_pack_report_input(
    proof_pack_id: str = Path(
        ...,
        description="Manage-owned immutable proof-pack identifier.",
        examples=["dpp_rr_001"],
    ),
) -> DpmProofPackGatewayResponse:
    return await dpm_proof_pack_service().get_proof_pack_report_input(
        proof_pack_id=proof_pack_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{proof_pack_id}/ai-evidence-input",
    response_model=DpmProofPackGatewayResponse,
    summary="Get DPM proof-pack AI evidence input",
    description=(
        "What: returns manage-owned deterministic AI-evidence input for one RFC-0040 proof pack. "
        "When: call this before asking lotus-ai for governed memo or narrative generation. How: "
        "Gateway preserves source refs, hashes, section states, and reason codes from manage and "
        "does not generate AI narrative itself."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_proof_pack_ai_evidence_input(
    proof_pack_id: str = Path(
        ...,
        description="Manage-owned immutable proof-pack identifier.",
        examples=["dpp_rr_001"],
    ),
) -> DpmProofPackGatewayResponse:
    return await dpm_proof_pack_service().get_proof_pack_ai_evidence_input(
        proof_pack_id=proof_pack_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{proof_pack_id}/ai-pm-memo",
    response_model=DpmProofPackMemoGatewayResponse,
    summary="Request proof-pack AI PM memo",
    description=(
        "What: requests a governed lotus-ai PM memo workflow-pack run from manage-owned "
        "DPM proof-pack AI evidence. When: call this only after manage supportability shows AI "
        "evidence is available and the user needs review-gated PM/control support text. How: "
        "Gateway first reads manage's DpmProofPackAiEvidenceInput, then executes lotus-ai "
        "dpm_pm_memo.pack@v1 as lotus-gateway; Gateway does not generate narrative, score PMs, "
        "approve trades, contact clients, place orders, or invent evidence."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def request_proof_pack_pm_memo(
    request: DpmProofPackMemoRequest,
    proof_pack_id: str = Path(
        ...,
        description="Manage-owned immutable proof-pack identifier for the bounded AI handoff.",
        examples=["dpp_rr_001"],
    ),
) -> DpmProofPackMemoGatewayResponse:
    return await dpm_proof_pack_service().request_proof_pack_pm_memo(
        proof_pack_id=proof_pack_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )
