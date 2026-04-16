from typing import Any

from pydantic import BaseModel, Field


class IntakeBundleRequest(BaseModel):
    body: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw payload passed through to lotus-core ingestion /ingest/portfolio-bundle.",
    )


class EnvelopeResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request boundary.",
        examples=["corr-intake-1"],
    )
    contract_version: str = Field(
        description="Gateway contract version for the intake response.",
        examples=["v1"],
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Opaque lotus-core ingestion payload returned unchanged by gateway.",
    )


class LookupItem(BaseModel):
    id: str = Field(
        description="Stable lookup identifier returned to the UI selector.",
        examples=["PF_1001"],
    )
    label: str = Field(
        description="Advisor-facing lookup label shown in the UI selector.",
        examples=["PF_1001 | Alpha Growth"],
    )


class LookupResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request boundary.",
        examples=["corr-intake-2"],
    )
    contract_version: str = Field(
        description="Gateway contract version for the lookup response.",
        examples=["v1"],
    )
    items: list[LookupItem] = Field(
        default_factory=list,
        description="Selector-ready lookup entries returned by lotus-core through gateway.",
    )
