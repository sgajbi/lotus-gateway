from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceAdvisorBookMember(BaseModel):
    portfolio_id: str
    client_id: str
    booking_center_code: str
    portfolio_type: str
    status: str
    open_date: date
    close_date: date | None = None
    base_currency: str
    source_record_id: str
    membership_source: Literal["party_role_assignment", "legacy_advisor_projection"]
    role_type: str | None = None

    model_config = ConfigDict(extra="ignore")


class SourceAdvisorBookSupportability(BaseModel):
    state: Literal["READY", "INCOMPLETE"]
    reason: str
    returned_portfolio_count: int = Field(ge=0)
    filters_applied: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class SourceAdvisorBookResponse(BaseModel):
    product_name: Literal["PortfolioManagerBookMembership"]
    product_version: Literal["v1"]
    portfolio_manager_id: str
    tenant_id: str | None = None
    generated_at: datetime
    as_of_date: date
    latest_evidence_timestamp: datetime | None = None
    snapshot_id: str | None = None
    content_hash: str
    data_quality_status: str
    source_evidence_current: bool
    freshness_status: str
    booking_center_code: str | None = None
    members: list[SourceAdvisorBookMember] = Field(default_factory=list)
    supportability: SourceAdvisorBookSupportability
    lineage: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")
