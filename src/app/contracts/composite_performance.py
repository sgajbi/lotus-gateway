from typing import Any

from pydantic import BaseModel, Field


class CompositePerformanceTwrRequest(BaseModel):
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


class CompositePerformanceInspectionRequest(BaseModel):
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
