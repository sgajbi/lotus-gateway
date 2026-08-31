from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.report_ordering_examples import REPORT_ORDERING_RESPONSE_EXAMPLE

ReportAvailabilityState = Literal["ready", "partial", "unavailable"]
ReportEligibilityState = Literal[
    "ready",
    "partial",
    "unavailable",
    "permission_blocked",
    "unsupported",
]


class ReportOrderingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ReportOrderingAvailability(ReportOrderingModel):
    state: ReportAvailabilityState = Field(
        description="Source-backed availability of the report catalogue or report family."
    )
    reason_code: str = Field(
        alias="reasonCode",
        description="Stable business-safe reason for the current availability state.",
    )
    message: str = Field(description="Business-facing explanation of the availability state.")


class ReportScopeSelection(ReportOrderingModel):
    scope_type: Literal["portfolio", "client", "book"] = Field(
        alias="scopeType",
        description="Business scope selected for report ordering.",
    )
    scope_id: str = Field(
        alias="scopeId",
        min_length=1,
        description="Stable identifier for the selected portfolio, client, or advisor book.",
    )


class ReportOrderingEligibility(ReportOrderingModel):
    state: ReportEligibilityState = Field(
        description="Whether the caller and selected scope can use this ordering choice."
    )
    reason_code: str = Field(
        alias="reasonCode",
        description="Stable product-safe reason for the eligibility state.",
    )
    message: str = Field(description="Business-facing explanation of the eligibility state.")


class ReportSubmissionCapability(ReportOrderingModel):
    capability_id: Literal[
        "reporting.portfolio_review.single",
        "reporting.portfolio_review.explicit_batch",
    ] = Field(
        alias="capabilityId",
        description="Stable implemented Gateway submission capability.",
    )
    method: Literal["POST"]
    path: Literal["/api/v1/reports/portfolio-reviews", "/api/v1/report-batches"]
    state: ReportEligibilityState
    reason_code: str = Field(alias="reasonCode")


class ReportConfigurationOption(ReportOrderingModel):
    value: str
    business_label: str = Field(alias="businessLabel")


class ReportConfigurationField(ReportOrderingModel):
    field_id: str = Field(alias="fieldId")
    business_label: str = Field(alias="businessLabel")
    description: str
    input_type: Literal["business_date", "currency", "benchmark", "multi_select", "text"] = Field(
        alias="inputType"
    )
    requirement: Literal["required", "optional", "conditional"]
    defaulting_policy: str = Field(alias="defaultingPolicy")
    value_source: Literal[
        "caller",
        "portfolio_context_or_caller",
        "gateway_eligible_benchmark",
        "report_catalogue",
    ] = Field(alias="valueSource")
    options: list[ReportConfigurationOption] = Field(default_factory=list)


class ReportSectionAcceptedBrief(ReportOrderingModel):
    run_id: str = Field(
        alias="runId",
        description=(
            "Accepted advisor-brief run the order must carry as options.advisor_brief_run_id."
        ),
    )
    reviewed_by: str = Field(
        alias="reviewedBy",
        description="Actor recorded on the accepting review transition.",
    )
    reviewed_at: str = Field(
        alias="reviewedAt",
        description="Instant of the accepting review transition (UTC).",
    )


class ReportSectionAvailability(ReportOrderingModel):
    state: Literal["ready", "unavailable"] = Field(
        description="Source-backed availability of this section for the selected scope."
    )
    reason_code: str = Field(
        alias="reasonCode",
        description=(
            "Stable reason passed through from Reporting untranslated: "
            "advisor_brief_accepted, advisor_brief_not_reviewed, "
            "advisor_brief_context_mismatch, or advisor_brief_availability_unknown "
            "(the lookup could not answer - NOT proof that no accepted brief exists)."
        ),
    )
    message: str = Field(description="Business-facing explanation of the availability state.")
    accepted_brief: ReportSectionAcceptedBrief | None = Field(
        default=None,
        alias="acceptedBrief",
        description="Present exactly when state is ready: the brief the order would compose.",
    )


class ReportSection(ReportOrderingModel):
    section_id: str = Field(alias="sectionId")
    business_label: str = Field(alias="businessLabel")
    description: str
    display_order: int = Field(alias="displayOrder", ge=1)
    selection_posture: Literal["required", "optional"] = Field(alias="selectionPosture")
    default_selected: bool = Field(alias="defaultSelected")
    dependency_field_ids: list[str] = Field(alias="dependencyFieldIds", default_factory=list)
    availability: ReportSectionAvailability | None = Field(
        default=None,
        description=(
            "Scope-specific section availability, populated only when it was evaluated - "
            "today for ADVISOR_COMMENTARY under a single-portfolio scope selection. Absent "
            "means not evaluated (for example a client or book scope), never unavailable."
        ),
    )


class ReportOutputFormat(ReportOrderingModel):
    format_id: Literal["json", "pdf"] = Field(alias="formatId")
    business_label: str = Field(alias="businessLabel")
    use_posture: Literal["system_integration", "governed_document"] = Field(alias="usePosture")
    state: ReportAvailabilityState
    reason_code: str = Field(alias="reasonCode")


class ReportOrderingMode(ReportOrderingModel):
    mode_id: Literal[
        "single_portfolio",
        "explicit_portfolio_batch",
        "governed_schedule",
        "source_workflow",
    ] = Field(alias="modeId")
    business_label: str = Field(alias="businessLabel")
    description: str
    default_output_format: Literal["json", "pdf"] = Field(alias="defaultOutputFormat")
    interactive: bool
    eligibility: ReportOrderingEligibility
    submission: ReportSubmissionCapability | None = None


class ReportFamilyOrderingOption(ReportOrderingModel):
    report_family_id: str = Field(alias="reportFamilyId")
    business_label: str = Field(alias="businessLabel")
    description: str
    intended_use: str = Field(alias="intendedUse")
    audience_roles: list[str] = Field(alias="audienceRoles")
    client_release_posture: Literal[
        "advisor_review_required_distribution_not_supported",
        "internal_control_only",
    ] = Field(alias="clientReleasePosture")
    ordering_modes: list[ReportOrderingMode] = Field(alias="orderingModes")
    output_formats: list[ReportOutputFormat] = Field(alias="outputFormats")
    configuration_fields: list[ReportConfigurationField] = Field(
        alias="configurationFields", default_factory=list
    )
    sections: list[ReportSection] = Field(default_factory=list)
    availability: ReportOrderingAvailability
    eligibility: ReportOrderingEligibility


class WorkbenchReportOrderingResponse(ReportOrderingModel):
    contract_version: Literal["workbench-report-ordering.v1"] = Field(
        default="workbench-report-ordering.v1",
        alias="contractVersion",
        description="Version of the Workbench-facing report ordering contract.",
    )
    source_authority: Literal["reporting"] = Field(
        default="reporting",
        alias="sourceAuthority",
        description="Business authority that owns report configuration and lifecycle truth.",
    )
    source_contract_version: Literal["report-ordering-catalogue.v1"] = Field(
        default="report-ordering-catalogue.v1",
        alias="sourceContractVersion",
    )
    scope_selection: ReportScopeSelection | None = Field(default=None, alias="scopeSelection")
    catalogue_availability: ReportOrderingAvailability = Field(alias="catalogueAvailability")
    scope_eligibility: ReportOrderingEligibility = Field(alias="scopeEligibility")
    report_families: list[ReportFamilyOrderingOption] = Field(alias="reportFamilies")

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={"example": REPORT_ORDERING_RESPONSE_EXAMPLE},
    )
