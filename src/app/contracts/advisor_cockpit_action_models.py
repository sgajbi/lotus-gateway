"""Typed, source-faithful read models for Advisor Cockpit actions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AdvisorCockpitActionStatus = Literal[
    "READY",
    "PENDING_REVIEW",
    "BLOCKED",
    "ACKNOWLEDGED",
    "HANDOFF_REQUESTED",
    "COMPLETED",
    "SUPERSEDED",
]
AdvisorCockpitActionPriority = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]
AdvisorCockpitOwnerRole = Literal[
    "ADVISOR",
    "DESK_HEAD",
    "COMPLIANCE_REVIEWER",
    "INVESTMENT_DESK",
    "PORTFOLIO_MANAGER",
    "OPERATIONS",
    "CRM_OWNER",
    "REPORTING_OWNER",
    "ARCHIVE_OWNER",
    "EXECUTION_OWNER",
    "SYSTEM",
]
AdvisorCockpitActionFamily = Literal[
    "CLIENT_MEETING_PREPARATION",
    "PROPOSAL_READY_FOR_REVIEW",
    "PROPOSAL_BLOCKED_BY_SOURCE_GAP",
    "POLICY_REVIEW_REQUIRED",
    "APPROVAL_DEPENDENCY_AGING",
    "CLIENT_CONSENT_REQUIRED",
    "MEMO_PACKAGE_BLOCKED",
    "REPORT_RENDER_ARCHIVE_BLOCKED",
    "EXECUTION_HANDOFF_READY",
    "EXECUTION_STATUS_ATTENTION",
    "HOUSE_VIEW_IMPACT_REVIEW",
    "WORKSPACE_DRAFT_STALE",
    "CLIENT_FOLLOW_UP_REQUIRED",
    "SUPPORTABILITY_DEGRADED",
    "UNSUPPORTED_CAPABILITY",
]
AdvisorCockpitSlaAgeBand = Literal[
    "NOT_DUE",
    "DUE_SOON",
    "DUE_NOW",
    "OVERDUE",
    "CRITICAL_OVERDUE",
    "NOT_APPLICABLE",
]
AdvisorCockpitEvidenceAccessClass = Literal[
    "CUSTOMER_CONSUMABLE_SUMMARY",
    "RESTRICTED_CUSTOMER_EVIDENCE",
    "OPERATOR_ONLY_SUPPORTABILITY",
    "INTERNAL_ONLY_DIAGNOSTICS",
]
AdvisorCockpitDependencyState = Literal["READY", "DEGRADED", "UNAVAILABLE", "NOT_CONFIGURED"]
AdvisorCockpitUnsupportedCapability = Literal[
    "CLIENT_READY_PUBLICATION",
    "EXTERNAL_CLIENT_COMMUNICATION",
    "CRM_SYSTEM_OF_RECORD",
    "CALENDAR_SCHEDULING",
    "OMS_ORDER_LIFECYCLE",
    "COMPLETED_POLICY_APPROVAL_AUTHORITY",
    "COMPLETED_POLICY_SIGN_OFF_AUTHORITY",
    "FULL_RFC0028_DEMO_RFP_PACKAGE",
]

_IDENTIFIER_MAX_LENGTH = 160
_TEXT_MAX_LENGTH = 1000
_SUMMARY_MAX_LENGTH = 512
_LIST_MAX_ITEMS = 64


class _StrictActionContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AdvisorCockpitActionEvidenceRef(_StrictActionContractModel):
    evidence_id: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    evidence_type: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    source_system: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    access_class: AdvisorCockpitEvidenceAccessClass
    summary: str = Field(min_length=1, max_length=_SUMMARY_MAX_LENGTH)


class AdvisorCockpitActionLineageRef(_StrictActionContractModel):
    lineage_id: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    source_system: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    content_hash: str | None = Field(
        default=None,
        min_length=1,
        max_length=_IDENTIFIER_MAX_LENGTH,
    )


class AdvisorCockpitActionSourceReadinessGap(_StrictActionContractModel):
    source_family: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    gap_code: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    owner_role: AdvisorCockpitOwnerRole
    message: str = Field(min_length=1, max_length=_SUMMARY_MAX_LENGTH)


class AdvisorCockpitActionDependencyReadiness(_StrictActionContractModel):
    dependency: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    state: AdvisorCockpitDependencyState
    reason_code: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    summary: str = Field(min_length=1, max_length=_SUMMARY_MAX_LENGTH)


class AdvisorCockpitActionAcknowledgementState(_StrictActionContractModel):
    acknowledged: bool
    acknowledgement_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=_IDENTIFIER_MAX_LENGTH,
    )
    acknowledged_by: str | None = Field(
        default=None,
        min_length=1,
        max_length=_IDENTIFIER_MAX_LENGTH,
    )
    acknowledged_at: str | None = Field(default=None, min_length=1)
    acknowledgement_note: str | None = Field(
        default=None, min_length=1, max_length=_SUMMARY_MAX_LENGTH
    )


class AdvisorCockpitActionItem(_StrictActionContractModel):
    action_item_id: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    action_item_version: int = Field(ge=1)
    action_family: AdvisorCockpitActionFamily
    status: AdvisorCockpitActionStatus
    priority: AdvisorCockpitActionPriority
    owner_role: AdvisorCockpitOwnerRole
    owner_role_label: str = Field(min_length=1, max_length=_SUMMARY_MAX_LENGTH)
    owning_system: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    title: str = Field(min_length=1, max_length=_SUMMARY_MAX_LENGTH)
    next_required_action: str = Field(min_length=1, max_length=_TEXT_MAX_LENGTH)
    reason_codes: list[str] = Field(default_factory=list, max_length=_LIST_MAX_ITEMS)
    client_ref: str | None = Field(default=None, min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    household_ref: str | None = Field(default=None, min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    portfolio_id: str | None = Field(default=None, min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    proposal_id: str | None = Field(default=None, min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    workspace_id: str | None = Field(default=None, min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    memo_id: str | None = Field(default=None, min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    policy_evaluation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=_IDENTIFIER_MAX_LENGTH,
    )
    report_ref: str | None = Field(default=None, min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    execution_ref: str | None = Field(default=None, min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    due_at: str | None = Field(default=None, min_length=1)
    sla_age_band: AdvisorCockpitSlaAgeBand
    materiality_rank: int = Field(default=0, ge=0)
    source_timestamp: str | None = Field(
        default=None, min_length=1, max_length=_IDENTIFIER_MAX_LENGTH
    )
    evidence_refs: list[AdvisorCockpitActionEvidenceRef] = Field(
        default_factory=list,
        max_length=_LIST_MAX_ITEMS,
    )
    source_readiness_gaps: list[AdvisorCockpitActionSourceReadinessGap] = Field(
        default_factory=list,
        max_length=_LIST_MAX_ITEMS,
    )
    dependency_readiness: list[AdvisorCockpitActionDependencyReadiness] = Field(
        default_factory=list,
        max_length=_LIST_MAX_ITEMS,
    )
    lineage_refs: list[AdvisorCockpitActionLineageRef] = Field(
        default_factory=list,
        max_length=_LIST_MAX_ITEMS,
    )
    acknowledgement_state: AdvisorCockpitActionAcknowledgementState = Field(
        default_factory=lambda: AdvisorCockpitActionAcknowledgementState(acknowledged=False),
    )
    unsupported_capabilities: list[AdvisorCockpitUnsupportedCapability] = Field(
        default_factory=list,
        max_length=_LIST_MAX_ITEMS,
    )
    correlation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=_IDENTIFIER_MAX_LENGTH,
    )


class AdvisorCockpitActionPage(_StrictActionContractModel):
    items: list[AdvisorCockpitActionItem] = Field(max_length=_LIST_MAX_ITEMS)
    next_cursor: str | None = Field(
        default=None,
        min_length=1,
        max_length=_IDENTIFIER_MAX_LENGTH,
    )
    page_size: int = Field(ge=1, le=100)
    total_count: int | None = Field(default=None, ge=0)


__all__ = [
    "AdvisorCockpitActionAcknowledgementState",
    "AdvisorCockpitActionDependencyReadiness",
    "AdvisorCockpitActionEvidenceRef",
    "AdvisorCockpitActionFamily",
    "AdvisorCockpitActionItem",
    "AdvisorCockpitActionLineageRef",
    "AdvisorCockpitActionPage",
    "AdvisorCockpitActionPriority",
    "AdvisorCockpitActionSourceReadinessGap",
    "AdvisorCockpitActionStatus",
    "AdvisorCockpitDependencyState",
    "AdvisorCockpitEvidenceAccessClass",
    "AdvisorCockpitOwnerRole",
    "AdvisorCockpitSlaAgeBand",
    "AdvisorCockpitUnsupportedCapability",
]
