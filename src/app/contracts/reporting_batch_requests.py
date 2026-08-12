from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PortfolioBatchCandidate(BaseModel):
    portfolio_id: str = Field(
        ...,
        description="Portfolio identifier from lotus-core portfolio scope.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    tenant_id: str = Field(
        ..., description="Tenant that owns the portfolio.", examples=["tenant-sg"]
    )
    region: str = Field(..., description="Region that owns the portfolio.", examples=["APAC"])
    active: bool = Field(..., description="Whether the portfolio is active.", examples=[True])
    selected: bool = Field(
        False,
        description="Whether selected-subset materialization includes this portfolio.",
        examples=[True],
    )
    source_system: str = Field(
        "lotus-core",
        description="Authoritative source system for the portfolio candidate.",
        examples=["lotus-core"],
    )
    source_object: str = Field(
        "PortfolioScope",
        description="Authoritative source object or API contract for the candidate.",
        examples=["PortfolioScope"],
    )


class BatchCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector_mode: Literal["explicit_portfolio_list"] = Field(
        ...,
        description="Portfolio selector mode used to materialize batch items.",
        examples=["explicit_portfolio_list"],
    )
    portfolio_ids: list[str] = Field(
        min_length=1,
        max_length=1000,
        description=(
            "Portfolio identifiers requested from the authenticated caller's source-owned book."
        ),
        examples=[["PB_SG_GLOBAL_BAL_001"]],
    )
    as_of_date: date = Field(
        ...,
        description="Business as-of date for all materialized batch items.",
        examples=["2026-04-22"],
    )
    requested_output_formats: list[str] = Field(
        default_factory=lambda: ["pdf"],
        description="Requested output formats for each report job.",
        examples=[["pdf"]],
    )
    reporting_currency: str | None = Field(
        default=None,
        description="Reporting currency passed into each report job.",
        examples=["USD"],
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Report options that affect every materialized batch item.",
        examples=[{"sections": ["OVERVIEW", "PERFORMANCE"]}],
    )
    max_batch_size: int = Field(
        250,
        ge=1,
        le=1000,
        description="Maximum number of materialized items allowed for this request.",
        examples=[250],
    )

    @field_validator("portfolio_ids")
    @classmethod
    def validate_portfolio_ids(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("portfolio_ids must not contain blank values")
        if len(set(normalized)) != len(normalized):
            raise ValueError("portfolio_ids must not contain duplicates")
        return normalized

    @model_validator(mode="after")
    def validate_batch_size(self) -> "BatchCreateRequest":
        if len(self.portfolio_ids) > self.max_batch_size:
            raise ValueError("portfolio_ids exceed max_batch_size")
        return self


class ReportBatchMaterializationRequest(BatchCreateRequest):
    source_candidates: list[PortfolioBatchCandidate] = Field(
        min_length=1,
        description=(
            "Gateway-resolved portfolio candidates forwarded only after source-owned membership "
            "verification."
        ),
    )
