from typing import Any

from fastapi import APIRouter, Path

from app.clients.dpm_client import DpmClient
from app.config import settings
from app.contracts.dpm_proof_packs import (
    DpmProofPackErrorDetail,
    DpmProofPackGatewayResponse,
    DpmProofPackGenerateRequest,
    DpmProofPackMarkdownResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.dpm_proof_pack_service import DpmProofPackService

router = APIRouter(
    prefix="/api/v1/dpm/command-center/proof-packs",
    tags=["DPM Command Center"],
)
_UPSTREAM_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {
        "model": DpmProofPackErrorDetail,
        "description": "lotus-manage could not find the requested proof pack or source.",
    },
    409: {
        "model": DpmProofPackErrorDetail,
        "description": "lotus-manage rejected the proof-pack request as conflicting.",
    },
    422: {
        "model": DpmProofPackErrorDetail,
        "description": "lotus-manage rejected the proof-pack payload as invalid.",
    },
    503: {
        "model": DpmProofPackErrorDetail,
        "description": "lotus-manage proof-pack authority is unavailable or degraded.",
    },
}


def _dpm_proof_pack_service() -> DpmProofPackService:
    return DpmProofPackService(
        dpm_client=DpmClient(
            base_url=settings.management_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
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
    return await _dpm_proof_pack_service().generate_proof_pack(
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
    return await _dpm_proof_pack_service().get_proof_pack(
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
    return await _dpm_proof_pack_service().get_proof_pack_markdown(
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
    return await _dpm_proof_pack_service().get_proof_pack_report_input(
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
    return await _dpm_proof_pack_service().get_proof_pack_ai_evidence_input(
        proof_pack_id=proof_pack_id,
        correlation_id=correlation_id_var.get(),
    )
