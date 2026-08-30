from app.contracts.report_ordering import ReportScopeSelection
from app.contracts.report_ordering_source import SourceReportOrderingCatalogue
from app.services.report_ordering_eligibility import ReportOrderingEntitlements
from app.services.report_ordering_projection import (
    project_report_ordering_catalogue,
    unavailable_report_ordering_response,
)


def _source() -> SourceReportOrderingCatalogue:
    return SourceReportOrderingCatalogue.model_validate(
        {
            "source_service": "lotus-report",
            "contract_version": "report-ordering-catalogue.v1",
            "report_families": [
                _family("portfolio_review", ["client_advisor", "portfolio_manager"]),
                _family("proof_pack", ["portfolio_manager"], mode_id="source_workflow"),
            ],
            "supportability": {
                "state": "partial",
                "reason_code": "report_catalogue_partially_available",
                "message": "Some report outputs are unavailable.",
            },
        }
    )


def _family(family_id: str, roles: list[str], mode_id: str = "single_portfolio"):
    return {
        "report_family_id": family_id,
        "business_label": "Portfolio review report",
        "description": "Governed report evidence.",
        "intended_use": "advisor_client_portfolio_review",
        "audience_roles": roles,
        "client_release_posture": (
            "advisor_review_required_distribution_not_supported"
            if family_id == "portfolio_review"
            else "internal_control_only"
        ),
        "ordering_modes": [
            {
                "mode_id": mode_id,
                "business_label": "Mode",
                "description": "Create report evidence.",
                "default_output_format": "json",
                "interactive": mode_id == "single_portfolio",
            }
        ],
        "output_formats": [
            {
                "format_id": "json",
                "business_label": "Structured data package",
                "use_posture": "system_integration",
                "state": "ready",
                "reason_code": "report_data_ready",
            },
            {
                "format_id": "pdf",
                "business_label": "Governed PDF document",
                "use_posture": "governed_document",
                "state": "unavailable",
                "reason_code": "render_metadata_unavailable",
            },
        ],
        "supportability": {
            "state": "partial",
            "reason_code": "report_family_partially_available",
            "message": "Available with reduced formats.",
        },
    }


def _entitlements(role: str) -> ReportOrderingEntitlements:
    return ReportOrderingEntitlements.from_headers(
        {
            "X-Role": role,
            "X-Caller-Portfolio-Ids": "portfolio-1",
        }
    )


def test_client_advisor_sees_only_audience_relevant_report_family() -> None:
    response = project_report_ordering_catalogue(
        source=_source(),
        selection=ReportScopeSelection(scope_type="portfolio", scope_id="portfolio-1"),
        entitlements=_entitlements("client_advisor"),
    )

    serialized = response.model_dump(by_alias=True, mode="json")

    assert response.catalogue_availability.state == "partial"
    assert response.scope_eligibility.state == "ready"
    assert [item.report_family_id for item in response.report_families] == ["portfolio_review"]
    assert serialized["reportFamilies"][0]["outputFormats"][1] == {
        "formatId": "pdf",
        "businessLabel": "Governed PDF document",
        "usePosture": "governed_document",
        "state": "unavailable",
        "reasonCode": "render_metadata_unavailable",
    }
    assert "sourceService" not in serialized


def test_portfolio_manager_sees_source_workflow_without_direct_submission() -> None:
    response = project_report_ordering_catalogue(
        source=_source(),
        selection=ReportScopeSelection(scope_type="portfolio", scope_id="portfolio-1"),
        entitlements=_entitlements("portfolio_manager"),
    )

    proof_pack = response.report_families[1]

    assert proof_pack.report_family_id == "proof_pack"
    assert proof_pack.ordering_modes[0].eligibility.state == "unsupported"
    assert proof_pack.ordering_modes[0].submission is None


def test_unknown_business_role_receives_no_internal_report_families() -> None:
    response = project_report_ordering_catalogue(
        source=_source(),
        selection=ReportScopeSelection(scope_type="portfolio", scope_id="portfolio-1"),
        entitlements=_entitlements("service_officer"),
    )

    assert response.scope_eligibility.state == "permission_blocked"
    assert response.scope_eligibility.reason_code == "report_ordering_role_not_entitled"
    assert response.report_families == []


def test_unavailable_response_is_typed_and_contains_no_source_payload() -> None:
    response = unavailable_report_ordering_response(
        selection=ReportScopeSelection(scope_type="portfolio", scope_id="portfolio-1"),
        entitlements=_entitlements("client_advisor"),
        reason_code="report_catalogue_contract_invalid",
        message="Report choices are temporarily unavailable.",
    )

    assert response.catalogue_availability.state == "unavailable"
    assert response.scope_eligibility.state == "ready"
    assert response.report_families == []


def test_projection_carries_advisor_commentary_vocabulary() -> None:
    """lotus-report's catalogue now publishes the ADVISOR_COMMENTARY section
    with its conditional advisor_brief_run_id text field (report PR #204).
    The source and workbench contracts must both accept the extended
    vocabulary and pass it through unchanged - a Literal miss here fails the
    entire ordering surface closed as report_catalogue_contract_invalid."""

    family = _family("portfolio_review", ["client_advisor"])
    family["configuration_fields"] = [
        {
            "field_id": "advisor_brief_run_id",
            "business_label": "Accepted Advisor Brief run",
            "description": "Accepted brief run identity for the commentary section.",
            "input_type": "text",
            "requirement": "conditional",
            "defaulting_policy": "caller_required",
            "value_source": "caller",
        }
    ]
    family["sections"] = [
        {
            "section_id": "ADVISOR_COMMENTARY",
            "business_label": "Advisor commentary",
            "description": "Reviewed advisor narrative from an accepted brief.",
            "display_order": 25,
            "selection_posture": "optional",
            "default_selected": False,
            "dependency_field_ids": ["advisor_brief_run_id"],
        }
    ]
    source = SourceReportOrderingCatalogue.model_validate(
        {
            "source_service": "lotus-report",
            "contract_version": "report-ordering-catalogue.v1",
            "report_families": [family],
            "supportability": {
                "state": "ready",
                "reason_code": "report_catalogue_ready",
                "message": "Available.",
            },
        }
    )

    response = project_report_ordering_catalogue(
        source=source,
        selection=None,
        entitlements=_entitlements("client_advisor"),
    )

    projected = response.report_families[0]
    field = next(
        item for item in projected.configuration_fields if item.field_id == "advisor_brief_run_id"
    )
    assert field.input_type == "text"
    assert field.requirement == "conditional"
    section = next(item for item in projected.sections if item.section_id == "ADVISOR_COMMENTARY")
    assert section.selection_posture == "optional"
    assert section.default_selected is False
    assert section.dependency_field_ids == ["advisor_brief_run_id"]
