"""Advisor-book attention facts composed from Advise-owned cockpit action items.

Two independently admitted scopes meet here: Core owns the book membership cohort
(portfolio_manager_id) and lotus-advise owns the action feed (authorized advisor scope).
Gateway intersects them on portfolio identity only — it never asserts the two caller
identities are the same principal, and it counts source-owned actionable items without
reinterpreting their status, priority, or reasons.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.contracts.advisor_book import AdvisorBookScope


class AdvisorBookPortfolioAttention(BaseModel):
    portfolio_id: str = Field(
        description="Portfolio identifier from the trusted Core book membership cohort.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    action_count: int = Field(
        ge=0,
        description=(
            "Number of Advise-owned cockpit action items bound to this portfolio in the "
            "caller's admitted Advise scope. A lower bound when coverage is partial."
        ),
        examples=[2],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        max_length=3,
        description=(
            "Up to three distinct Advise-owned reason codes, in the source's own action "
            "ordering. Gateway does not rank or reinterpret them."
        ),
        examples=[["PROPOSAL_READY_FOR_REVIEW"]],
    )


class AdvisorBookAttentionSummary(BaseModel):
    portfolio_count: int = Field(
        ge=0,
        description="Number of active portfolios in the trusted membership cohort.",
        examples=[2],
    )
    portfolios_with_actions: int = Field(
        ge=0,
        description="Cohort members with at least one counted action item.",
        examples=[1],
    )
    action_count: int = Field(
        ge=0,
        description="Counted action items bound to cohort members.",
        examples=[3],
    )
    unassigned_action_count: int = Field(
        ge=0,
        description=(
            "Counted action items in the caller's Advise scope that carry no portfolio "
            "identity (for example client- or household-level items)."
        ),
        examples=[1],
    )
    outside_book_action_count: int = Field(
        ge=0,
        description=(
            "Counted action items bound to a portfolio outside the trusted membership "
            "cohort. Preserved as an explicit count rather than silently dropped."
        ),
        examples=[0],
    )
    source_stated_total: int | None = Field(
        default=None,
        ge=0,
        description="Total action count stated by lotus-advise for the caller's scope.",
        examples=[4],
    )
    coverage_state: Literal["complete", "partial", "not_read"] = Field(
        description=(
            "complete: every source action page was read. partial: the bounded page budget "
            "was reached before the source feed ended, so every count is a lower bound. "
            "not_read: the action feed was not read at all (empty book), so the zero "
            "unassigned/outside counts are not statements about the feed."
        ),
        examples=["complete"],
    )
    coverage_reason: Literal[
        "action_feed_fully_read",
        "action_page_budget_reached",
        "empty_book_feed_not_read",
    ] = Field(
        description="Why the coverage state holds.",
        examples=["action_feed_fully_read"],
    )
    state: Literal["supported", "empty"] = Field(
        description="empty only when the trusted membership cohort has no members.",
        examples=["supported"],
    )


class AdvisorBookAttentionSource(BaseModel):
    source_service: Literal["lotus-advise"] = Field(
        description="Service that owns the action items.",
        examples=["lotus-advise"],
    )
    source_route: Literal["/advisory/cockpit/actions"] = Field(
        description="Advise route family that owns the advisor action feed.",
        examples=["/advisory/cockpit/actions"],
    )
    scope_basis: Literal["advise_authorized_advisor_scope"] = Field(
        default="advise_authorized_advisor_scope",
        description=(
            "The action feed is admitted under the caller's Advise advisor scope, "
            "independently of the Core membership scope; the two are intersected on "
            "portfolio identity only."
        ),
    )
    membership_as_of_date: date = Field(
        description=(
            "Business date used for the Core membership cohort. Action items are "
            "current-state facts from lotus-advise and carry no as-of semantics."
        ),
        examples=["2026-04-10"],
    )


class AdvisorBookAttentionResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque request correlation identifier.",
        examples=["corr-advisor-book-attention-001"],
    )
    contract_version: Literal["v1"] = Field(
        default="v1",
        description="Version of the Gateway advisor-book attention contract.",
        examples=["v1"],
    )
    scope: AdvisorBookScope
    summary: AdvisorBookAttentionSummary
    items: list[AdvisorBookPortfolioAttention] = Field(
        default_factory=list,
        description=(
            "One entry per trusted cohort member in stable membership order, including "
            "zero-count members."
        ),
    )
    source: AdvisorBookAttentionSource
