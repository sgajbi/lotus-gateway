from datetime import datetime

from pydantic import BaseModel, Field


class ReportingSnapshotResponse(BaseModel):
    correlation_id: str = Field(
        ...,
        alias="correlationId",
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-reporting-1"],
    )
    contract_version: str = Field(
        ...,
        alias="contractVersion",
        description="Gateway contract version for the reporting response.",
        examples=["v1"],
    )
    source_service: str = Field(
        ...,
        alias="sourceService",
        description="Upstream source service that produced the reporting payload.",
        examples=["lotus-report"],
    )
    portfolio_id: str = Field(
        ...,
        alias="portfolioId",
        description="Canonical portfolio identifier for the reporting snapshot.",
        examples=["DEMO_DPM_EUR_001"],
    )
    as_of_date: str = Field(
        ...,
        alias="asOfDate",
        description="Business as-of date used to resolve the reporting snapshot.",
        examples=["2026-02-24"],
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="UTC timestamp when the upstream reporting snapshot was generated.",
        examples=["2026-02-24T07:00:00Z"],
    )
    rows: list[dict] = Field(
        default_factory=list,
        description="Report-ready snapshot rows returned by lotus-report for the portfolio/date.",
    )

    model_config = {"populate_by_name": True}


class ReportingSummaryResponse(BaseModel):
    correlation_id: str = Field(
        ...,
        alias="correlationId",
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-reporting-2"],
    )
    contract_version: str = Field(
        ...,
        alias="contractVersion",
        description="Gateway contract version for the reporting response.",
        examples=["v1"],
    )
    source_service: str = Field(
        ...,
        alias="sourceService",
        description="Upstream source service that produced the reporting payload.",
        examples=["lotus-report"],
    )
    portfolio_id: str = Field(
        ...,
        alias="portfolioId",
        description="Canonical portfolio identifier for the reporting summary.",
        examples=["DEMO_DPM_EUR_001"],
    )
    as_of_date: str = Field(
        ...,
        alias="asOfDate",
        description="Business as-of date resolved from the reporting request payload.",
        examples=["2026-02-24"],
    )
    data: dict = Field(
        default_factory=dict,
        description="Opaque lotus-report summary payload returned unchanged by gateway.",
    )

    model_config = {"populate_by_name": True}


class ReportingReviewResponse(BaseModel):
    correlation_id: str = Field(
        ...,
        alias="correlationId",
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-reporting-3"],
    )
    contract_version: str = Field(
        ...,
        alias="contractVersion",
        description="Gateway contract version for the reporting response.",
        examples=["v1"],
    )
    source_service: str = Field(
        ...,
        alias="sourceService",
        description="Upstream source service that produced the reporting payload.",
        examples=["lotus-report"],
    )
    portfolio_id: str = Field(
        ...,
        alias="portfolioId",
        description="Canonical portfolio identifier for the reporting review payload.",
        examples=["DEMO_DPM_EUR_001"],
    )
    as_of_date: str = Field(
        ...,
        alias="asOfDate",
        description="Business as-of date resolved from the reporting request payload.",
        examples=["2026-02-24"],
    )
    data: dict = Field(
        default_factory=dict,
        description="Opaque lotus-report review payload returned unchanged by gateway.",
    )

    model_config = {"populate_by_name": True}
