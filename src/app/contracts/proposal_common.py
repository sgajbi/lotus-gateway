from pydantic import BaseModel, Field


class ProposalEnvelopeBase(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-proposals-2"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the proposal envelope response.",
        examples=["v1"],
    )
