from app.contracts.report_ordering import ReportOrderingEligibility, ReportScopeSelection
from app.contracts.report_ordering_source import SourceReportFamily, SourceReportOrderingMode
from app.services.report_ordering_eligibility import (
    ReportOrderingEntitlements,
    family_eligibility,
    mode_eligibility,
    scope_eligibility,
    submission_capability,
)


def _entitlements(**headers: str) -> ReportOrderingEntitlements:
    return ReportOrderingEntitlements.from_headers(headers)


def _selection(scope_type: str = "portfolio", scope_id: str = "portfolio-1"):
    return ReportScopeSelection(scope_type=scope_type, scope_id=scope_id)


def _family(*, family_id: str = "portfolio_review", roles: list[str] | None = None):
    return SourceReportFamily.model_validate(
        {
            "report_family_id": family_id,
            "business_label": "Portfolio review report",
            "description": "Review pack.",
            "intended_use": "advisor_client_portfolio_review",
            "audience_roles": roles or ["client_advisor"],
            "client_release_posture": "advisor_review_required_distribution_not_supported",
            "ordering_modes": [
                {
                    "mode_id": "single_portfolio",
                    "business_label": "Single portfolio",
                    "description": "Create one report.",
                    "default_output_format": "json",
                    "interactive": True,
                }
            ],
            "output_formats": [
                {
                    "format_id": "json",
                    "business_label": "Structured data package",
                    "use_posture": "system_integration",
                    "state": "ready",
                    "reason_code": "report_data_ready",
                }
            ],
            "supportability": {
                "state": "ready",
                "reason_code": "report_family_ready",
                "message": "Ready.",
            },
        }
    )


def _mode(mode_id: str) -> SourceReportOrderingMode:
    return SourceReportOrderingMode(
        mode_id=mode_id,
        business_label="Mode",
        description="Mode description.",
        default_output_format="json",
        interactive=mode_id == "single_portfolio",
    )


def test_scope_eligibility_requires_role_before_scope_selection() -> None:
    result = scope_eligibility(
        selection=_selection(),
        entitlements=_entitlements(**{"X-Caller-Portfolio-Ids": "portfolio-1"}),
    )

    assert result.state == "permission_blocked"
    assert result.reason_code == "caller_role_missing"


def test_scope_eligibility_requires_explicit_selection() -> None:
    result = scope_eligibility(
        selection=None,
        entitlements=_entitlements(**{"X-Role": "client_advisor"}),
    )

    assert result.state == "unavailable"
    assert result.reason_code == "scope_selection_required"


def test_scope_eligibility_rejects_cross_scope_selection() -> None:
    result = scope_eligibility(
        selection=_selection(scope_id="portfolio-2"),
        entitlements=_entitlements(
            **{
                "X-Role": "client_advisor",
                "X-Caller-Portfolio-Ids": "portfolio-1",
            }
        ),
    )

    assert result.state == "permission_blocked"
    assert result.reason_code == "selected_scope_not_entitled"


def test_scope_eligibility_accepts_trimmed_multi_value_entitlements() -> None:
    result = scope_eligibility(
        selection=_selection(scope_id="portfolio-2"),
        entitlements=_entitlements(
            **{
                "X-Role": "client_advisor, portfolio_manager",
                "X-Caller-Portfolio-Ids": "portfolio-1, portfolio-2",
            }
        ),
    )

    assert result.state == "ready"


def test_family_eligibility_applies_source_audience_roles() -> None:
    result = family_eligibility(
        family=_family(roles=["portfolio_manager"]),
        entitlements=_entitlements(**{"X-Role": "client_advisor"}),
        selected_scope_eligibility=ReportOrderingEligibility(
            state="ready",
            reason_code="selected_scope_eligible",
            message="Ready.",
        ),
    )

    assert result.state == "permission_blocked"
    assert result.reason_code == "report_family_role_not_entitled"


def test_single_portfolio_mode_exposes_only_implemented_submission() -> None:
    family = _family()
    eligibility = mode_eligibility(
        family=family,
        mode=_mode("single_portfolio"),
        selection=_selection(),
        eligible_family=ReportOrderingEligibility(
            state="ready",
            reason_code="report_family_eligible",
            message="Ready.",
        ),
    )

    submission = submission_capability(
        family=family,
        mode=_mode("single_portfolio"),
        eligibility=eligibility,
    )

    assert eligibility.state == "ready"
    assert submission is not None
    assert submission.path == "/api/v1/reports/portfolio-reviews"


def test_batch_mode_requires_authoritative_explicit_portfolio_selection() -> None:
    family = _family()
    eligibility = mode_eligibility(
        family=family,
        mode=_mode("explicit_portfolio_batch"),
        selection=_selection(scope_type="book", scope_id="book-1"),
        eligible_family=ReportOrderingEligibility(
            state="ready",
            reason_code="report_family_eligible",
            message="Ready.",
        ),
    )

    submission = submission_capability(
        family=family,
        mode=_mode("explicit_portfolio_batch"),
        eligibility=eligibility,
    )

    assert eligibility.state == "partial"
    assert eligibility.reason_code == "explicit_portfolio_selection_required"
    assert submission is not None
    assert submission.path == "/api/v1/report-batches"


def test_source_workflow_has_no_direct_gateway_submission() -> None:
    family = _family(family_id="proof_pack", roles=["portfolio_manager"])
    eligibility = mode_eligibility(
        family=family,
        mode=_mode("source_workflow"),
        selection=_selection(),
        eligible_family=ReportOrderingEligibility(
            state="ready",
            reason_code="report_family_eligible",
            message="Ready.",
        ),
    )

    assert eligibility.state == "unsupported"
    assert (
        submission_capability(
            family=family,
            mode=_mode("source_workflow"),
            eligibility=eligibility,
        )
        is None
    )
