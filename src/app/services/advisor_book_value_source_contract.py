from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceAdvisorBookValueScope(BaseModel):
    portfolio_ids: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class SourceAdvisorBookValuePortfolio(BaseModel):
    portfolio_id: str
    aum_reporting_currency: Decimal
    position_count: int = Field(ge=0)

    model_config = ConfigDict(extra="ignore")


class SourceAdvisorBookValueTotals(BaseModel):
    portfolio_count: int = Field(ge=0)
    position_count: int = Field(ge=0)
    aum_reporting_currency: Decimal

    model_config = ConfigDict(extra="ignore")


class SourceAdvisorBookValueResponse(BaseModel):
    scope_type: Literal["portfolio_list"]
    scope: SourceAdvisorBookValueScope
    resolved_as_of_date: date
    reporting_currency: str
    totals: SourceAdvisorBookValueTotals
    portfolios: list[SourceAdvisorBookValuePortfolio] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")
