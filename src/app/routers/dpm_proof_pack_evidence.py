from fastapi import APIRouter, Path

from app.contracts.dpm_proof_packs import DpmProofPackMarkdownResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_proof_pack_common import UPSTREAM_PROOF_PACK_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_proof_pack_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/proof-packs",
    tags=["DPM Command Center"],
)


async def _get_proof_pack_markdown(
    *,
    proof_pack_id: str,
) -> DpmProofPackMarkdownResponse:
    return await dpm_proof_pack_service().get_proof_pack_markdown(
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
    responses=UPSTREAM_PROOF_PACK_ERROR_RESPONSES,
)
async def get_proof_pack_markdown(
    proof_pack_id: str = Path(
        ...,
        description="Manage-owned immutable proof-pack identifier.",
        examples=["dpp_rr_001"],
    ),
) -> DpmProofPackMarkdownResponse:
    return await _get_proof_pack_markdown(proof_pack_id=proof_pack_id)
