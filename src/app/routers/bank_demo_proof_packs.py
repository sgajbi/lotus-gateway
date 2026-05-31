from typing import Any

from fastapi import APIRouter, Body, Header

from app.contracts.bank_demo_proof import BankDemoProofEnvelopeResponse
from app.routers.bank_demo_proof_common import (
    BANK_DEMO_PROOF_RESPONSES,
    bank_demo_correlation_id,
)
from app.services.advisory_service_provider import bank_demo_proof_service

router = APIRouter(prefix="/api/v1/advisory/bank-demo-proof", tags=["bank-demo-proof"])


@router.post(
    "/proof-packs",
    response_model=BankDemoProofEnvelopeResponse,
    summary="Build RFC-0028 Backend Proof Pack",
    description=(
        "Forwards RFC-0028 proof-pack capture requests to lotus-advise and returns the sanitized "
        "proof bundle in a Gateway envelope. Advise remains proof authority; Gateway only "
        "propagates correlation, problem status, and source-owned proof content."
    ),
    responses=BANK_DEMO_PROOF_RESPONSES,
)
async def build_bank_demo_proof_pack(
    body: dict[str, Any] = Body(
        ...,
        description=(
            "lotus-advise RFC-0028 proof-pack capture request containing governed live runtime "
            "evidence and sanitized runtime posture."
        ),
    ),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> BankDemoProofEnvelopeResponse:
    return await bank_demo_proof_service().build_proof_pack(
        body=body,
        correlation_id=bank_demo_correlation_id(x_correlation_id),
    )
