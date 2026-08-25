from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AllocationContributorType = Literal["direct_position", "look_through_component"]
LookThroughMode = Literal["direct_only", "prefer_look_through"]


class SourceAllocationContributor(BaseModel):
    contributor_type: AllocationContributorType
    portfolio_id: str
    security_id: str
    booked_security_id: str
    source_snapshot_id: int
    component_record_id: int | None
    component_weight: Decimal | None
    component_effective_from: date | None
    component_effective_to: date | None
    component_source_system: str | None
    component_source_record_id: str | None
    market_value_reporting_currency: Decimal
    bucket_weight: Decimal | None

    model_config = ConfigDict(extra="ignore")


class SourceAllocationBucket(BaseModel):
    dimension_value: str
    market_value_reporting_currency: Decimal
    weight: Decimal
    position_count: int = Field(ge=0)
    contributor_count: int = Field(ge=0)
    contributors: list[SourceAllocationContributor]
    contributors_truncated: bool
    omitted_market_value_reporting_currency: Decimal

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_contributor_reconciliation(self) -> "SourceAllocationBucket":
        if len(self.contributors) > self.contributor_count:
            raise ValueError("contributors cannot exceed contributor_count")
        if not self.contributors_truncated and len(self.contributors) != self.contributor_count:
            raise ValueError("untruncated contributors must contain every source row")
        retained_value = sum(
            (item.market_value_reporting_currency for item in self.contributors),
            Decimal("0"),
        )
        if retained_value + self.omitted_market_value_reporting_currency != (
            self.market_value_reporting_currency
        ):
            raise ValueError("contributors and omitted residual must reconcile to bucket value")
        return self


class SourceAllocationView(BaseModel):
    dimension: str
    buckets: list[SourceAllocationBucket]

    model_config = ConfigDict(extra="ignore")


class SourceAllocationLookThrough(BaseModel):
    requested_mode: LookThroughMode
    applied_mode: LookThroughMode
    supported: bool
    decomposed_position_count: int = Field(ge=0)
    limitation_reason: str | None

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "LookThroughMode",
    "SourceAllocationBucket",
    "SourceAllocationContributor",
    "SourceAllocationLookThrough",
    "SourceAllocationView",
]
