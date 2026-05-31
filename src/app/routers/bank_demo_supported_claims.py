from fastapi import APIRouter, Header

from app.contracts.bank_demo_proof import BankDemoProofEnvelopeResponse
from app.routers.bank_demo_proof_common import (
    BANK_DEMO_PROOF_RESPONSES,
    bank_demo_correlation_id,
)
from app.services.advisory_service_provider import bank_demo_proof_service

router = APIRouter(prefix="/api/v1/advisory/bank-demo-proof", tags=["bank-demo-proof"])


@router.get(
    "/supported-claim-register",
    response_model=BankDemoProofEnvelopeResponse,
    summary="Get RFC-0028 Supported-Claim Register",
    description=(
        "Returns the source-owned RFC-0028 supported-claim register from lotus-advise. Gateway "
        "does not promote planned, unsupported, backend-only, screenshot, RFP, or client-ready "
        "claims; it preserves Advise classifications and wording rules for Workbench and demo "
        "automation."
    ),
    responses=BANK_DEMO_PROOF_RESPONSES,
)
async def get_bank_demo_supported_claim_register(
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> BankDemoProofEnvelopeResponse:
    return await bank_demo_proof_service().get_supported_claim_register(
        correlation_id=bank_demo_correlation_id(x_correlation_id),
    )
