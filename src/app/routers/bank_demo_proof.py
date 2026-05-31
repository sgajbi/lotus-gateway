from fastapi import APIRouter, Header

from app.contracts.bank_demo_proof import BankDemoProofEnvelopeResponse
from app.routers.bank_demo_proof_common import (
    BANK_DEMO_PROOF_RESPONSES,
    bank_demo_correlation_id,
)
from app.services.advisory_service_provider import bank_demo_proof_service

router = APIRouter(prefix="/api/v1/advisory/bank-demo-proof", tags=["bank-demo-proof"])


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
    return await bank_demo_proof_service().get_scenario_contract(
        correlation_id=bank_demo_correlation_id(x_correlation_id),
    )
