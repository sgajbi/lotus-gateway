"""Primary Advisor Book workspace contract: one dense, per-fact-truthful composition.

Membership is resolved exactly once from Core for the requested business date; the
resulting cohort and its provenance are frozen, and every composed fact — Core bulk
value facts and Advise action-item facts — is stated against exactly that cohort under
one elapsed composition deadline. A row exists for every trusted cohort member and never
disappears because an enrichment source degraded: a degraded source degrades its own
fact block (and the rows' entries for that fact) with an explicit bounded reason, while
every other stated fact survives.

The action feed is admitted under the caller's Advise advisor scope, independently of
the Core membership scope, and the two are intersected on portfolio identity only. An
absent or non-advisor Advise scope is not an error for the workspace: the action fact is
explicitly unavailable and the value composition still stands.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.contracts.advisor_book import AdvisorBookProvenance, AdvisorBookScope
from app.contracts.advisor_book_action_items import (
    AdvisorBookActionItemsSource,
    AdvisorBookActionItemsSummary,
    AdvisorBookPortfolioActionItems,
)
from app.contracts.advisor_book_summary import (
    AdvisorBookValueItem,
    AdvisorBookValueSource,
    AdvisorBookValueSummary,
)

AdvisorBookWorkspaceValueReason = Literal[
    "value_facts_stated",
    "value_source_unavailable",
    "value_source_contract_invalid",
    "composition_deadline_reached",
]
AdvisorBookWorkspaceActionReason = Literal[
    "action_facts_stated",
    "advise_scope_not_presented",
    "advise_scope_invalid",
    "advise_scope_not_advisor",
    "action_feed_unavailable",
]


class AdvisorBookWorkspaceValueFacts(BaseModel):
    state: Literal["stated", "unavailable"] = Field(
        description=(
            "stated: Core answered the bounded bulk value read for the frozen cohort and "
            "the summary preserves Core's own coverage posture (which may itself be "
            "partial or fail-closed). unavailable: the value read failed or the "
            "composition deadline stopped it; no value fact is invented."
        ),
        examples=["stated"],
    )
    reason_code: AdvisorBookWorkspaceValueReason = Field(
        description="Bounded reason for the value fact-block state.",
        examples=["value_facts_stated"],
    )
    summary: AdvisorBookValueSummary | None = Field(
        default=None,
        description="Book-level value summary; present exactly when state is stated.",
    )
    source: AdvisorBookValueSource | None = Field(
        default=None,
        description="Value source descriptor; present exactly when state is stated.",
    )

    @model_validator(mode="after")
    def _stated_iff_facts_present(self) -> "AdvisorBookWorkspaceValueFacts":
        stated = self.state == "stated"
        if stated != (self.summary is not None and self.source is not None):
            raise ValueError("value facts must be present exactly when state is stated")
        if stated != (self.reason_code == "value_facts_stated"):
            raise ValueError("value reason_code must match the fact-block state")
        return self


class AdvisorBookWorkspaceActionFacts(BaseModel):
    state: Literal["stated", "unavailable"] = Field(
        description=(
            "stated: the Advise action feed was read under the caller's admitted advisor "
            "scope and the summary preserves the read's explicit coverage (complete or "
            "partial lower bound). unavailable: the caller presented no usable advisor "
            "scope or the feed read failed; no count is invented and zero is never "
            "implied."
        ),
        examples=["stated"],
    )
    reason_code: AdvisorBookWorkspaceActionReason = Field(
        description="Bounded reason for the action fact-block state.",
        examples=["action_facts_stated"],
    )
    summary: AdvisorBookActionItemsSummary | None = Field(
        default=None,
        description="Book-level action-item summary; present exactly when state is stated.",
    )
    source: AdvisorBookActionItemsSource | None = Field(
        default=None,
        description="Action source descriptor; present exactly when state is stated.",
    )

    @model_validator(mode="after")
    def _stated_iff_facts_present(self) -> "AdvisorBookWorkspaceActionFacts":
        stated = self.state == "stated"
        if stated != (self.summary is not None and self.source is not None):
            raise ValueError("action facts must be present exactly when state is stated")
        if stated != (self.reason_code == "action_facts_stated"):
            raise ValueError("action reason_code must match the fact-block state")
        return self


class AdvisorBookWorkspaceRow(BaseModel):
    portfolio_id: str = Field(
        description="Portfolio identifier from the frozen Core membership cohort.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    value: AdvisorBookValueItem | None = Field(
        default=None,
        description=(
            "Per-member value fact from Core's bulk read; null exactly when the value "
            "fact block is unavailable. An untrustworthy member coverage state is a "
            "present fact with state unavailable, not a missing row."
        ),
    )
    action_items: AdvisorBookPortfolioActionItems | None = Field(
        default=None,
        description=(
            "Per-member action-item fact from the Advise feed read; null exactly when "
            "the action fact block is unavailable. Counts are lower bounds whenever the "
            "action summary states partial coverage."
        ),
    )

    @model_validator(mode="after")
    def _facts_bind_to_this_row(self) -> "AdvisorBookWorkspaceRow":
        if self.value is not None and self.value.portfolio_id != self.portfolio_id:
            raise ValueError("value fact is bound to a different portfolio")
        if self.action_items is not None and self.action_items.portfolio_id != self.portfolio_id:
            raise ValueError("action-item fact is bound to a different portfolio")
        return self


class AdvisorBookWorkspaceResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque request correlation identifier.",
        examples=["corr-advisor-book-workspace-001"],
    )
    contract_version: Literal["v1"] = Field(
        default="v1",
        description="Version of the Gateway advisor-book workspace contract.",
        examples=["v1"],
    )
    scope: AdvisorBookScope
    rows: list[AdvisorBookWorkspaceRow] = Field(
        default_factory=list,
        description=(
            "One row per frozen cohort member in stable membership order. Rows never "
            "disappear because an enrichment source degraded."
        ),
    )
    value_facts: AdvisorBookWorkspaceValueFacts
    action_facts: AdvisorBookWorkspaceActionFacts
    membership_provenance: AdvisorBookProvenance | None = Field(
        default=None,
        description=(
            "Core membership provenance (freshness, evidence currency, lineage) for the "
            "frozen cohort every composed fact was stated against."
        ),
    )
