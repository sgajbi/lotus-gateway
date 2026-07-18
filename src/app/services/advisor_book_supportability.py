from dataclasses import dataclass
from typing import Literal

from app.contracts.advisor_book import AdvisorBookSupportability
from app.services.advisor_book_source_contract import SourceAdvisorBookResponse

_BASE_LIMITATIONS = (
    "delegated_scope_not_supported",
    "team_scope_not_supported",
    "household_scope_not_supported",
    "assets_under_management_not_reported",
    "attention_indicators_not_reported",
)


@dataclass(frozen=True)
class _AdvisorBookSupportContext:
    tenant_scope: Literal["source_confirmed", "trusted_context_only"]
    limitations: tuple[str, ...]
    has_legacy_projection: bool


def advisor_book_supportability(
    *, source: SourceAdvisorBookResponse, filtered_count: int
) -> AdvisorBookSupportability:
    context = _support_context(source)
    if not source.members:
        return AdvisorBookSupportability(
            state="empty",
            reason_code="advisor_book_empty",
            tenant_scope=context.tenant_scope,
            limitations=list(context.limitations),
        )
    reason_code: Literal[
        "advisor_book_source_incomplete",
        "advisor_book_tenant_scope_not_reported",
        "advisor_book_legacy_projection",
    ]
    limitations = list(context.limitations)
    if source.supportability.state == "INCOMPLETE":
        limitations.append("source_membership_incomplete")
        reason_code = "advisor_book_source_incomplete"
    elif source.tenant_id is None:
        reason_code = "advisor_book_tenant_scope_not_reported"
    elif context.has_legacy_projection:
        reason_code = "advisor_book_legacy_projection"
    elif filtered_count == 0:
        return AdvisorBookSupportability(
            state="empty",
            reason_code="advisor_book_filter_empty",
            tenant_scope=context.tenant_scope,
            limitations=list(context.limitations),
        )
    else:
        return AdvisorBookSupportability(
            state="ready",
            reason_code="advisor_book_ready",
            tenant_scope=context.tenant_scope,
            limitations=list(context.limitations),
        )
    return AdvisorBookSupportability(
        state="degraded",
        reason_code=reason_code,
        tenant_scope=context.tenant_scope,
        limitations=limitations,
    )


def empty_advisor_book_supportability() -> AdvisorBookSupportability:
    return AdvisorBookSupportability(
        state="empty",
        reason_code="advisor_book_empty",
        tenant_scope="trusted_context_only",
        limitations=["tenant_scope_not_reported", *_BASE_LIMITATIONS],
    )


def _support_context(source: SourceAdvisorBookResponse) -> _AdvisorBookSupportContext:
    limitations = list(_BASE_LIMITATIONS)
    has_legacy_projection = any(
        member.membership_source == "legacy_advisor_projection" for member in source.members
    )
    if has_legacy_projection:
        limitations.append("legacy_advisor_projection_present")
    tenant_scope: Literal["source_confirmed", "trusted_context_only"] = "source_confirmed"
    if source.tenant_id is None:
        limitations.insert(0, "tenant_scope_not_reported")
        tenant_scope = "trusted_context_only"
    return _AdvisorBookSupportContext(
        tenant_scope=tenant_scope,
        limitations=tuple(limitations),
        has_legacy_projection=has_legacy_projection,
    )
