from typing import Any

from fastapi import APIRouter, Body, Header, status

from app.contracts.bank_demo_proof import BankDemoProofEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_factory import build_bank_demo_proof_service
from app.services.bank_demo_proof_service import BankDemoProofService

router = APIRouter(prefix="/api/v1/advisory/bank-demo-proof", tags=["bank-demo-proof"])

BANK_DEMO_PROOF_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_409_CONFLICT: {
        "description": (
            "lotus-advise rejected proof capture because material evidence does not match the "
            "canonical RFC-0028 scenario."
        )
    },
    422: {"description": "lotus-advise rejected the proof contract request shape."},
}


def _bank_demo_proof_service() -> BankDemoProofService:
    return build_bank_demo_proof_service()


def _correlation_id(x_correlation_id: str | None) -> str:
    return x_correlation_id or correlation_id_var.get() or ""


@router.get(
    "/scenario-contract",
    response_model=BankDemoProofEnvelopeResponse,
    summary="Get RFC-0028 Demo Scenario Contract",
    description=(
        "Returns the source-owned RFC-0028 bank-demo scenario contract from lotus-advise. "
        "Gateway preserves scenario ids, evidence requirements, Workbench panel requirements, "
        "and unsupported boundaries without creating advisory proof truth locally."
    ),
    responses=BANK_DEMO_PROOF_RESPONSES,
)
async def get_bank_demo_scenario_contract(
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> BankDemoProofEnvelopeResponse:
    return await _bank_demo_proof_service().get_scenario_contract(
        correlation_id=_correlation_id(x_correlation_id),
    )


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
    return await _bank_demo_proof_service().get_supported_claim_register(
        correlation_id=_correlation_id(x_correlation_id),
    )


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
    return await _bank_demo_proof_service().build_proof_pack(
        body=body,
        correlation_id=_correlation_id(x_correlation_id),
    )
