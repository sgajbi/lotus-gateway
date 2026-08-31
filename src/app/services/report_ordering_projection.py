from app.contracts.report_ordering import (
    ReportFamilyOrderingOption,
    ReportOrderingAvailability,
    ReportOrderingEligibility,
    ReportOrderingMode,
    ReportScopeSelection,
    ReportSectionAvailability,
    WorkbenchReportOrderingResponse,
)
from app.contracts.report_ordering_source import (
    SourceReportFamily,
    SourceReportOrderingCatalogue,
    SourceReportOrderingMode,
    SourceReportSupportability,
)
from app.services.report_ordering_eligibility import (
    ReportOrderingEntitlements,
    family_eligibility,
    mode_eligibility,
    scope_eligibility,
    submission_capability,
)


def project_report_ordering_catalogue(
    *,
    source: SourceReportOrderingCatalogue,
    selection: ReportScopeSelection | None,
    entitlements: ReportOrderingEntitlements,
    advisor_commentary_availability: ReportSectionAvailability | None = None,
) -> WorkbenchReportOrderingResponse:
    selected_scope_eligibility = scope_eligibility(
        selection=selection,
        entitlements=entitlements,
    )
    visible_families = [
        family
        for family in source.report_families
        if entitlements.roles.intersection(family.audience_roles)
    ]
    if entitlements.roles and not visible_families:
        selected_scope_eligibility = ReportOrderingEligibility(
            state="permission_blocked",
            reasonCode="report_ordering_role_not_entitled",
            message="No report families are available for the caller's business role.",
        )
    return WorkbenchReportOrderingResponse(
        scopeSelection=selection,
        catalogueAvailability=_availability(source.supportability),
        scopeEligibility=selected_scope_eligibility,
        reportFamilies=[
            _project_family(
                family,
                selection=selection,
                entitlements=entitlements,
                selected_scope_eligibility=selected_scope_eligibility,
                advisor_commentary_availability=advisor_commentary_availability,
            )
            for family in visible_families
        ],
    )


def unavailable_report_ordering_response(
    *,
    selection: ReportScopeSelection | None,
    entitlements: ReportOrderingEntitlements,
    reason_code: str,
    message: str,
) -> WorkbenchReportOrderingResponse:
    return WorkbenchReportOrderingResponse(
        scopeSelection=selection,
        catalogueAvailability=ReportOrderingAvailability(
            state="unavailable",
            reasonCode=reason_code,
            message=message,
        ),
        scopeEligibility=scope_eligibility(
            selection=selection,
            entitlements=entitlements,
        ),
        reportFamilies=[],
    )


def _project_family(
    family: SourceReportFamily,
    *,
    selection: ReportScopeSelection | None,
    entitlements: ReportOrderingEntitlements,
    selected_scope_eligibility: ReportOrderingEligibility,
    advisor_commentary_availability: ReportSectionAvailability | None = None,
) -> ReportFamilyOrderingOption:
    eligible_family = family_eligibility(
        family=family,
        entitlements=entitlements,
        selected_scope_eligibility=selected_scope_eligibility,
    )
    ordering_modes = [
        _project_mode(
            family,
            mode,
            selection=selection,
            eligible_family=eligible_family,
        )
        for mode in family.ordering_modes
    ]
    sections = [section.model_dump(mode="json") for section in family.sections]
    if advisor_commentary_availability is not None:
        for section in sections:
            if section.get("section_id") == "ADVISOR_COMMENTARY":
                section["availability"] = advisor_commentary_availability.model_dump(
                    mode="json", by_alias=True
                )
    return ReportFamilyOrderingOption.model_validate(
        {
            **family.model_dump(
                exclude={"ordering_modes", "supportability", "sections"},
                mode="json",
            ),
            "sections": sections,
            "ordering_modes": ordering_modes,
            "availability": _availability(family.supportability),
            "eligibility": eligible_family,
        }
    )


def _project_mode(
    family: SourceReportFamily,
    mode: SourceReportOrderingMode,
    *,
    selection: ReportScopeSelection | None,
    eligible_family: ReportOrderingEligibility,
) -> ReportOrderingMode:
    eligibility = mode_eligibility(
        family=family,
        mode=mode,
        selection=selection,
        eligible_family=eligible_family,
    )
    eligibility = _apply_default_format_availability(family, mode, eligibility)
    return ReportOrderingMode.model_validate(
        {
            **mode.model_dump(mode="json"),
            "eligibility": eligibility,
            "submission": submission_capability(
                family=family,
                mode=mode,
                eligibility=eligibility,
            ),
        }
    )


def _apply_default_format_availability(
    family: SourceReportFamily,
    mode: SourceReportOrderingMode,
    eligibility: ReportOrderingEligibility,
) -> ReportOrderingEligibility:
    if eligibility.state != "ready":
        return eligibility
    output_format = next(
        (item for item in family.output_formats if item.format_id == mode.default_output_format),
        None,
    )
    if output_format is None or output_format.state == "unavailable":
        return ReportOrderingEligibility(
            state="partial",
            reasonCode="default_output_format_unavailable",
            message="Choose an available output format before submitting this report.",
        )
    if output_format.state == "partial":
        return ReportOrderingEligibility(
            state="partial",
            reasonCode=output_format.reason_code,
            message="The default output format is temporarily degraded.",
        )
    return eligibility


def _availability(
    source_supportability: SourceReportSupportability,
) -> ReportOrderingAvailability:
    return ReportOrderingAvailability.model_validate(source_supportability, from_attributes=True)
