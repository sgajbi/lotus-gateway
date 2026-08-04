from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

AdvisorBookMandateType = Literal["ADVISORY", "DISCRETIONARY"]


class AdvisorBookScope(BaseModel):
    kind: Literal["own_book"] = Field(
        description="Source-backed advisor-book scope represented by this response.",
        examples=["own_book"],
    )
    label: Literal["My book"] = Field(
        description="Business label for the authenticated advisor's own supported book scope.",
        examples=["My book"],
    )
    as_of_date: date = Field(
        description="Business date used by Core to resolve effective portfolio membership.",
        examples=["2026-04-10"],
    )
    booking_center_code: str = Field(
        description="Trusted caller booking center applied to the source membership request.",
        examples=["Singapore"],
    )


class AdvisorBookPortfolio(BaseModel):
    portfolio_id: str = Field(
        description="Canonical portfolio identifier in the authenticated advisor's source book.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    display_name: str = Field(
        description=(
            "Source-safe portfolio display label. The first-wave source uses the canonical "
            "portfolio identifier when it publishes no separate display name."
        ),
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    client_id: str = Field(
        description="Client identifier published by the Core book-membership source product.",
        examples=["CIF_SG_GLOBAL_BAL_001"],
    )
    base_currency: str = Field(
        description="Portfolio base currency from the source-owned membership row.",
        examples=["USD"],
    )
    booking_center_code: str = Field(
        description="Booking center from the source-owned membership row.",
        examples=["Singapore"],
    )
    mandate_type: AdvisorBookMandateType = Field(
        description=(
            "Supported portfolio or mandate classification verified from the source-owned "
            "membership row."
        ),
        examples=["DISCRETIONARY"],
    )
    status: str = Field(
        description="Portfolio lifecycle status from the source-owned membership row.",
        examples=["ACTIVE"],
    )
    opened_on: date = Field(
        description="Portfolio opening date carried by the source membership evidence.",
        examples=["2025-03-31"],
    )
    closed_on: date | None = Field(
        default=None,
        description="Portfolio closing date when reported by the source membership evidence.",
        examples=[None],
    )
    membership_source: Literal["PortfolioManagerBookMembership:v1"] = Field(
        description="Versioned Core source product that established this book membership.",
        examples=["PortfolioManagerBookMembership:v1"],
    )
    membership_reference: str = Field(
        description="Opaque source record reference retained for support and audit review.",
        examples=["portfolio:PB_SG_GLOBAL_BAL_001"],
    )
    membership_basis: Literal["governed_role_assignment", "legacy_advisor_projection"] = Field(
        description=(
            "Whether membership is established by a governed portfolio role or the bounded "
            "legacy advisor projection published by Core."
        ),
        examples=["governed_role_assignment"],
    )


class AdvisorBookPage(BaseModel):
    total_count: int = Field(
        ge=0,
        description="Total source memberships after supported Gateway filters are applied.",
        examples=[1],
    )
    offset: int = Field(
        ge=0,
        description="Zero-based result offset requested by the caller.",
        examples=[0],
    )
    limit: int = Field(
        ge=1,
        le=100,
        description="Maximum number of portfolio memberships returned on this page.",
        examples=[25],
    )
    returned_count: int = Field(
        ge=0,
        description="Number of portfolio memberships returned on this page.",
        examples=[1],
    )
    sort_by: Literal["portfolio_id", "client_id", "mandate_type"] = Field(
        description="Stable business field used for deterministic result ordering.",
        examples=["portfolio_id"],
    )
    sort_order: Literal["asc", "desc"] = Field(
        description="Direction applied to the deterministic result ordering.",
        examples=["asc"],
    )


class AdvisorBookSupportability(BaseModel):
    state: Literal["ready", "empty", "degraded"] = Field(
        description="Product-safe availability posture for the authenticated advisor book.",
        examples=["degraded"],
    )
    reason_code: Literal[
        "advisor_book_ready",
        "advisor_book_empty",
        "advisor_book_filter_empty",
        "advisor_book_source_incomplete",
        "advisor_book_tenant_scope_not_reported",
        "advisor_book_legacy_projection",
    ] = Field(
        description="Bounded reason explaining the advisor-book availability posture.",
        examples=["advisor_book_tenant_scope_not_reported"],
    )
    tenant_scope: Literal["source_confirmed", "trusted_context_only"] = Field(
        description=(
            "Whether Core confirmed tenant scope or Gateway only has trusted caller context. "
            "Trusted-context-only posture is not tenant-isolation certification."
        ),
        examples=["trusted_context_only"],
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Bounded no-claim limitations that remain for this first-wave scope.",
        examples=[["tenant_scope_not_reported", "delegated_scope_not_supported"]],
    )


class AdvisorBookProvenance(BaseModel):
    product_name: Literal["PortfolioManagerBookMembership"] = Field(
        description="Core source-data product name retained by Gateway.",
        examples=["PortfolioManagerBookMembership"],
    )
    product_version: Literal["v1"] = Field(
        description="Core source-data product version retained by Gateway.",
        examples=["v1"],
    )
    generated_at: datetime = Field(
        description="UTC timestamp when Core generated the source membership response.",
        examples=["2026-04-10T02:00:00Z"],
    )
    latest_evidence_timestamp: datetime | None = Field(
        default=None,
        description="Latest source membership evidence timestamp reported by Core.",
        examples=["2026-04-10T01:59:00Z"],
    )
    freshness_status: str = Field(
        description="Source-owned freshness posture retained without reinterpretation.",
        examples=["CURRENT"],
    )
    data_quality_status: str = Field(
        description="Source-owned data-quality posture retained without reinterpretation.",
        examples=["ACCEPTED"],
    )
    source_evidence_current: bool = Field(
        description="Whether Core considers the membership evidence current for the request.",
        examples=[True],
    )
    snapshot_id: str | None = Field(
        default=None,
        description="Deterministic source snapshot identity when Core publishes one.",
        examples=["pm_book_membership:2e7dfe0c"],
    )
    content_hash: str = Field(
        description="Source-owned deterministic membership content hash.",
        examples=["sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"],
    )
    lineage: dict[str, str] = Field(
        default_factory=dict,
        description="Bounded Core lineage fields retained for support and audit use.",
        examples=[{"source_field": "advisor_id", "source_owner": "lotus-core"}],
    )


class AdvisorBookResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque request correlation identifier.",
        examples=["corr-advisor-book-001"],
    )
    contract_version: Literal["v1"] = Field(
        default="v1",
        description="Version of the Gateway advisor-book experience contract.",
        examples=["v1"],
    )
    scope: AdvisorBookScope
    page: AdvisorBookPage
    items: list[AdvisorBookPortfolio] = Field(
        default_factory=list,
        description="Source-backed portfolio memberships on the requested result page.",
    )
    supportability: AdvisorBookSupportability
    provenance: AdvisorBookProvenance | None = Field(
        default=None,
        description=(
            "Bounded Core source provenance, absent only for an explicit empty source book."
        ),
    )


class AdvisorBookErrorResponse(BaseModel):
    code: str = Field(
        description="Stable product-safe advisor-book error code.",
        examples=["advisor_book_access_denied"],
    )
    message: str = Field(
        description="Product-safe error explanation without upstream response content.",
        examples=["Advisor-book access is not available for this caller."],
    )
    correlation_id: str = Field(
        description="Opaque request correlation identifier for support follow-up.",
        examples=["corr-advisor-book-001"],
    )
