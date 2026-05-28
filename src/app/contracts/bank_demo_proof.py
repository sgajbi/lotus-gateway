from typing import Any

from pydantic import BaseModel, Field


class BankDemoProofEnvelopeResponse(BaseModel):
    correlation_id: str = Field(
        alias="correlationId",
        description="Gateway correlation id propagated to lotus-advise for proof diagnostics.",
        examples=["corr-rfc0028-gateway-proof"],
    )
    contract_version: str = Field(
        alias="contractVersion",
        description="Gateway envelope contract version.",
        examples=["v1"],
    )
    data: dict[str, Any] = Field(
        description=(
            "Source-owned RFC-0028 proof contract, supported-claim register, or sanitized "
            "proof-pack payload returned by lotus-advise without Gateway-side reinterpretation."
        )
    )

    model_config = {"populate_by_name": True}
