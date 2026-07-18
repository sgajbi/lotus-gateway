from dataclasses import dataclass

from app.contracts.report_ordering import (
    ReportEligibilityState,
    ReportOrderingEligibility,
    ReportScopeSelection,
    ReportSubmissionCapability,
)
from app.contracts.report_ordering_source import (
    SourceReportFamily,
    SourceReportOrderingMode,
)


@dataclass(frozen=True)
class ReportOrderingEntitlements:
    roles: frozenset[str]
    portfolio_ids: frozenset[str]
    client_ids: frozenset[str]
    book_ids: frozenset[str]

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> "ReportOrderingEntitlements":
        return cls(
            roles=_csv_values(headers.get("X-Role")),
            portfolio_ids=_csv_values(headers.get("X-Caller-Portfolio-Ids")),
            client_ids=_csv_values(headers.get("X-Caller-Client-Ids")),
            book_ids=_csv_values(headers.get("X-Caller-Book-Ids")),
        )

    def ids_for_scope(self, scope_type: str) -> frozenset[str]:
        return {
            "portfolio": self.portfolio_ids,
            "client": self.client_ids,
            "book": self.book_ids,
        }[scope_type]


def scope_eligibility(
    *,
    selection: ReportScopeSelection | None,
    entitlements: ReportOrderingEntitlements,
) -> ReportOrderingEligibility:
    if not entitlements.roles:
        return _eligibility(
            "permission_blocked",
            "caller_role_missing",
            "Report ordering requires an entitled business role.",
        )
    if selection is None:
        return _eligibility(
            "unavailable",
            "scope_selection_required",
            "Select a portfolio, client, or advisor book to evaluate report ordering.",
        )
    entitled_ids = entitlements.ids_for_scope(selection.scope_type)
    if not entitled_ids:
        return _eligibility(
            "permission_blocked",
            f"{selection.scope_type}_entitlement_missing",
            f"The caller has no entitled {selection.scope_type} scope for report ordering.",
        )
    if selection.scope_id not in entitled_ids:
        return _eligibility(
            "permission_blocked",
            "selected_scope_not_entitled",
            "The selected scope is not available to the caller.",
        )
    return _eligibility(
        "ready",
        "selected_scope_eligible",
        f"The selected {selection.scope_type} is available for report ordering.",
    )


def family_eligibility(
    *,
    family: SourceReportFamily,
    entitlements: ReportOrderingEntitlements,
    selected_scope_eligibility: ReportOrderingEligibility,
) -> ReportOrderingEligibility:
    if not entitlements.roles.intersection(family.audience_roles):
        return _eligibility(
            "permission_blocked",
            "report_family_role_not_entitled",
            "This report family is not available for the caller's business role.",
        )
    if selected_scope_eligibility.state != "ready":
        return selected_scope_eligibility
    return _eligibility(
        "ready",
        "report_family_eligible",
        "This report family is available for the caller and selected scope.",
    )


def mode_eligibility(
    *,
    family: SourceReportFamily,
    mode: SourceReportOrderingMode,
    selection: ReportScopeSelection | None,
    eligible_family: ReportOrderingEligibility,
) -> ReportOrderingEligibility:
    if eligible_family.state != "ready":
        return eligible_family
    if family.report_family_id != "portfolio_review" or mode.mode_id == "source_workflow":
        return _eligibility(
            "unsupported",
            "source_workflow_only",
            "This report is created from its governed business workflow.",
        )
    if mode.mode_id == "governed_schedule":
        return _eligibility(
            "unsupported",
            "operations_managed_schedule",
            "This report is created from an operations-managed reporting schedule.",
        )
    if mode.mode_id == "single_portfolio":
        return _single_portfolio_eligibility(selection)
    return _explicit_batch_eligibility(selection)


def submission_capability(
    *,
    family: SourceReportFamily,
    mode: SourceReportOrderingMode,
    eligibility: ReportOrderingEligibility,
) -> ReportSubmissionCapability | None:
    if family.report_family_id != "portfolio_review":
        return None
    if mode.mode_id == "single_portfolio":
        return ReportSubmissionCapability(
            capabilityId="reporting.portfolio_review.single",
            method="POST",
            path="/api/v1/reports/portfolio-reviews",
            state=eligibility.state,
            reasonCode=eligibility.reason_code,
        )
    if mode.mode_id == "explicit_portfolio_batch":
        return ReportSubmissionCapability(
            capabilityId="reporting.portfolio_review.explicit_batch",
            method="POST",
            path="/api/v1/report-batches",
            state=eligibility.state,
            reasonCode=eligibility.reason_code,
        )
    return None


def _single_portfolio_eligibility(
    selection: ReportScopeSelection | None,
) -> ReportOrderingEligibility:
    if selection is None or selection.scope_type != "portfolio":
        return _eligibility(
            "unsupported",
            "single_portfolio_scope_required",
            "Select an entitled portfolio for single-portfolio report ordering.",
        )
    return _eligibility(
        "ready",
        "single_portfolio_ordering_ready",
        "This portfolio can be submitted for report creation.",
    )


def _explicit_batch_eligibility(
    selection: ReportScopeSelection | None,
) -> ReportOrderingEligibility:
    if selection is None:
        return _eligibility(
            "unavailable",
            "scope_selection_required",
            "Select an entitled scope before preparing a portfolio batch.",
        )
    return _eligibility(
        "partial",
        "explicit_portfolio_selection_required",
        "Select the entitled portfolios to include before submitting the report batch.",
    )


def _csv_values(value: str | None) -> frozenset[str]:
    if value is None:
        return frozenset()
    return frozenset(item.strip() for item in value.split(",") if item.strip())


def _eligibility(
    state: ReportEligibilityState,
    reason_code: str,
    message: str,
) -> ReportOrderingEligibility:
    return ReportOrderingEligibility(
        state=state,
        reasonCode=reason_code,
        message=message,
    )
