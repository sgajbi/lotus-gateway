from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def _normalize_reporting_currency(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if value != value.strip():
        raise ValueError("reporting_currency must not contain leading or trailing whitespace")
    if not value.isascii() or not value.isalpha():
        raise ValueError("reporting_currency must contain exactly three ASCII letters")
    return value.upper()


CompositeReportingCurrency = Annotated[
    str,
    Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$"),
    BeforeValidator(_normalize_reporting_currency),
]


class CompositePerformanceSelectors(BaseModel):
    model_config = ConfigDict(extra="forbid")

    restatement_sequence: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Explicit immutable member-return fact sequence. Omission or null delegates latest "
            "qualified numeric sequence selection to lotus-performance."
        ),
        examples=[1],
    )
    return_view: Literal["GROSS", "NET_ACTUAL", "NET_MODEL_FEE"] = Field(
        default="NET_ACTUAL",
        description=(
            "Source-owned fee-view identity for persisted facts. Omission delegates the "
            "NET_ACTUAL default to lotus-performance; selection does not calculate model fees."
        ),
        examples=["NET_ACTUAL"],
    )
    reporting_currency: CompositeReportingCurrency | None = Field(
        default=None,
        description=(
            "Persisted reporting-currency identity: exactly three ASCII letters, normalized "
            "to uppercase without trimming. Omission or null uses the source composite "
            "definition currency; Gateway performs no FX conversion."
        ),
        examples=["USD"],
    )


class CompositePerformanceTwrRequest(CompositePerformanceSelectors):
    calculation_id: str | None = Field(
        default=None,
        description=(
            "Optional caller-provided composite calculation identifier. When omitted, "
            "lotus-performance generates the idempotency and lineage identifier."
        ),
        examples=["7f2b08b0-58e5-49be-b3ef-7a9cfb0321ce"],
    )
    composite_id: str = Field(
        description=(
            "Stable private-banking composite identifier owned by the composite source authority."
        ),
        examples=["PB_GLOBAL_BALANCED_USD"],
    )
    period_start: str = Field(
        description="Inclusive composite calculation start date in ISO-8601 format.",
        examples=["2026-01-01"],
    )
    period_end: str = Field(
        description="Inclusive composite calculation end date in ISO-8601 format.",
        examples=["2026-03-31"],
    )


class CompositePerformanceInspectionRequest(CompositePerformanceSelectors):
    inspection_id: str | None = Field(
        default=None,
        description=(
            "Optional caller-provided inspection identifier. When omitted, lotus-performance "
            "generates the support and audit evidence identifier."
        ),
        examples=["8d1e37d2-aeca-488c-bd43-77dbf6739103"],
    )
    composite_id: str = Field(
        description="Stable private-banking composite identifier to inspect.",
        examples=["PB_GLOBAL_BALANCED_USD"],
    )
    period_start: str = Field(
        description="Inclusive inspection start date in ISO-8601 format.",
        examples=["2026-01-01"],
    )
    period_end: str = Field(
        description="Inclusive inspection end date in ISO-8601 format.",
        examples=["2026-03-31"],
    )


class CompositePerformanceGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Gateway correlation identifier propagated to lotus-performance.",
        examples=["corr-composite-performance-1"],
    )
    contract_version: str = Field(
        default="composite-performance-gateway.v1",
        description="Gateway response contract version for composite performance operations.",
        examples=["composite-performance-gateway.v1"],
    )
    source_service: str = Field(
        default="lotus-performance",
        description="Authoritative service that calculated or inspected the composite result.",
        examples=["lotus-performance"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-performance before Gateway response projection.",
        examples=[200],
    )
    data: dict[str, Any] = Field(
        description=(
            "Source-owned composite payload from lotus-performance. Gateway preserves this "
            "payload without recalculating returns, member weights, dispersion, findings, "
            "lineage, restatement evidence, or classified inspection artifacts."
        ),
        examples=[
            {
                "composite_id": "PB_GLOBAL_BALANCED_USD",
                "status": "READY",
                "methodology": "persisted_member_return_asset_weighted_twr_v1",
                "periods": [],
            }
        ],
    )
