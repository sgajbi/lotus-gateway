from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReportOrderingSourceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceReportConfigurationOption(ReportOrderingSourceModel):
    value: str
    business_label: str


class SourceReportConfigurationField(ReportOrderingSourceModel):
    field_id: str
    business_label: str
    description: str
    input_type: Literal["business_date", "currency", "benchmark", "multi_select", "text"]
    requirement: Literal["required", "optional", "conditional"]
    defaulting_policy: str
    value_source: Literal[
        "caller",
        "portfolio_context_or_caller",
        "gateway_eligible_benchmark",
        "report_catalogue",
    ]
    options: list[SourceReportConfigurationOption] = Field(default_factory=list)


class SourceReportSection(ReportOrderingSourceModel):
    section_id: str
    business_label: str
    description: str
    display_order: int = Field(ge=1)
    selection_posture: Literal["required", "optional"]
    default_selected: bool
    dependency_field_ids: list[str] = Field(default_factory=list)


class SourceReportOrderingMode(ReportOrderingSourceModel):
    mode_id: Literal[
        "single_portfolio",
        "explicit_portfolio_batch",
        "governed_schedule",
        "source_workflow",
    ]
    business_label: str
    description: str
    default_output_format: Literal["json", "pdf"]
    interactive: bool


class SourceReportOutputFormat(ReportOrderingSourceModel):
    format_id: Literal["json", "pdf"]
    business_label: str
    use_posture: Literal["system_integration", "governed_document"]
    state: Literal["ready", "partial", "unavailable"]
    reason_code: str


class SourceReportSupportability(ReportOrderingSourceModel):
    state: Literal["ready", "partial", "unavailable"]
    reason_code: str
    message: str


class SourceReportFamily(ReportOrderingSourceModel):
    report_family_id: str
    business_label: str
    description: str
    intended_use: str
    audience_roles: list[str]
    client_release_posture: Literal[
        "advisor_review_required_distribution_not_supported",
        "internal_control_only",
    ]
    ordering_modes: list[SourceReportOrderingMode]
    output_formats: list[SourceReportOutputFormat]
    configuration_fields: list[SourceReportConfigurationField] = Field(default_factory=list)
    sections: list[SourceReportSection] = Field(default_factory=list)
    supportability: SourceReportSupportability


class SourceReportOrderingCatalogue(ReportOrderingSourceModel):
    source_service: Literal["lotus-report"]
    contract_version: Literal["report-ordering-catalogue.v1"]
    report_families: list[SourceReportFamily]
    supportability: SourceReportSupportability
