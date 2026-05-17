from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ExternalOrderExecutionAcknowledgementRequest(BaseModel):
    as_of_date: str = Field(
        description=(
            "Portfolio as-of date for source-owned ExternalOrderExecutionAcknowledgement:v1 "
            "posture lookup."
        ),
        examples=["2026-05-18"],
    )
    tenant_id: str | None = Field(
        default=None,
        description="Optional tenant scope forwarded unchanged to lotus-core.",
        examples=["default"],
    )
    mandate_id: str | None = Field(
        default=None,
        description="Optional mandate identifier forwarded unchanged to lotus-core.",
        examples=["MANDATE_SG_001"],
    )
    execution_intent_id: str | None = Field(
        default=None,
        description=(
            "Optional execution intent identifier forwarded unchanged. Gateway does not create "
            "or certify execution intent."
        ),
        examples=["exec-intent-001"],
    )
    order_reference_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Optional upstream order reference identifiers forwarded unchanged. Gateway does not "
            "generate orders or infer acknowledgement state from these identifiers."
        ),
        examples=[["order-ref-001"]],
    )

    model_config = ConfigDict(extra="allow")


class ExternalOrderExecutionAcknowledgementSupportability(BaseModel):
    state: Literal["UNAVAILABLE"] = Field(
        description=(
            "Core-owned supportability state. This source product is fail-closed until bank-owned "
            "external OMS acknowledgement feeds are ingested and certified."
        ),
        examples=["UNAVAILABLE"],
    )
    reason: str = Field(
        description="Core-owned reason code for the fail-closed acknowledgement posture.",
        examples=["EXTERNAL_OMS_SOURCE_NOT_INGESTED"],
    )
    acknowledgement_count: int = Field(
        description=(
            "Core-owned count of available acknowledgements; fail-closed posture returns 0."
        ),
        examples=[0],
    )
    missing_data_families: list[str] = Field(
        description="Core-owned missing data families preserved unchanged by Gateway.",
        examples=[["external_oms_order_execution_acknowledgement"]],
    )
    blocked_capabilities: list[str] = Field(
        description=(
            "Core-owned blocked capabilities preserved unchanged. These are supportability "
            "blockers, not Gateway-generated workflow decisions."
        ),
        examples=[
            [
                "order_generation",
                "venue_routing",
                "best_execution",
                "oms_acknowledgement",
                "fills",
                "settlement",
                "execution_status_certification",
                "autonomous_execution",
            ]
        ],
    )

    model_config = ConfigDict(extra="allow")


class ExternalOrderExecutionAcknowledgementResponse(BaseModel):
    product_name: Literal["ExternalOrderExecutionAcknowledgement"] = Field(
        description="Core source product name preserved by Gateway.",
        examples=["ExternalOrderExecutionAcknowledgement"],
    )
    product_version: Literal["v1"] = Field(
        description="Core source product version preserved by Gateway.",
        examples=["v1"],
    )
    portfolio_id: str = Field(description="Portfolio identifier from the Core source product.")
    client_id: str | None = Field(
        default=None,
        description="Client identifier from the Core source product when supplied.",
    )
    mandate_id: str | None = Field(
        default=None,
        description="Mandate identifier from the Core source product when supplied.",
    )
    execution_intent_id: str | None = Field(
        default=None,
        description="Execution intent identifier echoed from Core when supplied.",
    )
    order_reference_ids: list[str] = Field(
        default_factory=list,
        description="Order reference identifiers echoed from Core.",
    )
    acknowledgements: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Core-owned acknowledgement evidence. Gateway does not synthesize OMS "
            "acknowledgements, fills, settlement, or execution status."
        ),
    )
    supportability: ExternalOrderExecutionAcknowledgementSupportability = Field(
        description="Core-owned fail-closed supportability posture preserved by Gateway."
    )
    lineage: dict[str, Any] = Field(
        default_factory=dict,
        description="Core-owned lineage and non-claims preserved unchanged by Gateway.",
    )

    model_config = ConfigDict(extra="allow")
