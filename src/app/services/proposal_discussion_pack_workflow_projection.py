from app.contracts.proposal_discussion_pack import (
    ProposalDiscussionConsentEvidence,
    ProposalDiscussionPackageEvidence,
    ProposalDiscussionPackageState,
)
from app.services.proposal_discussion_pack_errors import (
    raise_proposal_discussion_pack_contract_invalid,
    raise_proposal_discussion_pack_snapshot_conflict,
)
from app.services.proposal_discussion_pack_source_contract import (
    SourceDiscussionApprovals,
    SourceDiscussionDetail,
    SourceDiscussionReporting,
)
from app.services.proposal_discussion_pack_source_projection import (
    ProposalDiscussionSourceResponse,
    discussion_source_evidence,
)
from app.services.proposal_discussion_pack_source_validation import (
    validated_discussion_approvals,
    validated_discussion_delivery,
)

_AVAILABLE_REPORT_STATUSES = {
    "ARCHIVED",
    "COMPLETED",
    "COMPLETED_WITH_WARNINGS",
    "DATA_READY",
    "READY",
}
_PENDING_REPORT_STATUSES = {
    "ACCEPTED",
    "PENDING",
    "PENDING_ARCHIVE",
    "QUEUED",
    "REPORT_STATUS_UNAVAILABLE",
    "RUNNING",
}
_ATTENTION_REPORT_STATUSES = {
    "ARCHIVE_FAILED",
    "CANCELED",
    "CANCELLED",
    "FAILED",
    "REJECTED",
    "RENDER_FAILED",
    "REPORT_STATUS_INVALID",
}


def project_discussion_package(
    response: ProposalDiscussionSourceResponse,
    detail: SourceDiscussionDetail,
) -> ProposalDiscussionPackageEvidence:
    evidence = discussion_source_evidence(response, capability="report_package")
    if evidence.state != "supported":
        return ProposalDiscussionPackageEvidence(
            state=evidence.state,
            reason_code=evidence.reason_code,
            package_state="not_requested",
        )
    source = validated_discussion_delivery(response.payload, detail=detail)
    if source.reporting is None:
        return ProposalDiscussionPackageEvidence(
            state="not_available",
            reason_code="report_package_not_requested",
            package_state="not_requested",
        )
    return _available_package(source.reporting, detail)


def _available_package(
    reporting: SourceDiscussionReporting,
    detail: SourceDiscussionDetail,
) -> ProposalDiscussionPackageEvidence:
    package_state, reason_code = _package_status(reporting.status)
    current_version = reporting.related_version_no == detail.current_version.version_no
    return ProposalDiscussionPackageEvidence(
        state="supported" if current_version else "partial",
        reason_code=reason_code if current_version else "report_package_for_historical_version",
        package_state=package_state,
        report_request_id=reporting.report_request_id,
        report_reference_id=reporting.report_reference_id,
        generated_at=reporting.generated_at,
        related_version_no=reporting.related_version_no,
        includes_reviewed_narrative=reporting.include_reviewed_narrative,
        source_service="lotus-report",
    )


def _package_status(status: str) -> tuple[ProposalDiscussionPackageState, str]:
    normalized = status.upper()
    if normalized in _AVAILABLE_REPORT_STATUSES:
        return "available", "report_package_available"
    if normalized in _PENDING_REPORT_STATUSES:
        return "pending", "report_package_pending"
    if normalized in _ATTENTION_REPORT_STATUSES:
        return "attention", "report_package_requires_attention"
    raise_proposal_discussion_pack_contract_invalid()


def project_discussion_consent(
    response: ProposalDiscussionSourceResponse,
    detail: SourceDiscussionDetail,
) -> ProposalDiscussionConsentEvidence:
    evidence = discussion_source_evidence(response, capability="approval_and_consent_records")
    if evidence.state != "supported":
        return ProposalDiscussionConsentEvidence(
            state=evidence.state,
            reason_code=evidence.reason_code,
            consent_state="not_recorded",
        )
    source = validated_discussion_approvals(response.payload, detail=detail)
    return _current_version_consent(source, detail)


def _current_version_consent(
    source: SourceDiscussionApprovals,
    detail: SourceDiscussionDetail,
) -> ProposalDiscussionConsentEvidence:
    current = [
        item
        for item in source.approvals
        if item.approval_type == "CLIENT_CONSENT"
        and item.related_version_no == detail.current_version.version_no
    ]
    if current:
        latest = current[-1]
        return ProposalDiscussionConsentEvidence(
            state="supported",
            reason_code=(
                "client_consent_recorded" if latest.approved else "client_consent_declined"
            ),
            consent_state="approved" if latest.approved else "declined",
            approval_id=latest.approval_id,
            actor_id=latest.actor_id,
            occurred_at=latest.occurred_at,
            related_version_no=latest.related_version_no,
        )
    return _missing_current_version_consent(source)


def _missing_current_version_consent(
    source: SourceDiscussionApprovals,
) -> ProposalDiscussionConsentEvidence:
    uncorrelated = any(
        item.approval_type == "CLIENT_CONSENT" and item.related_version_no is None
        for item in source.approvals
    )
    return ProposalDiscussionConsentEvidence(
        state="partial" if uncorrelated else "supported",
        reason_code=(
            "client_consent_version_not_correlated"
            if uncorrelated
            else "client_consent_not_recorded"
        ),
        consent_state="not_recorded",
    )


def validate_discussion_consent_lifecycle(
    consent: ProposalDiscussionConsentEvidence,
    detail: SourceDiscussionDetail,
) -> None:
    if detail.proposal.current_state in {"EXECUTION_READY", "EXECUTED"} and (
        consent.state != "supported" or consent.consent_state != "approved"
    ):
        raise_proposal_discussion_pack_snapshot_conflict()
    if consent.state != "supported":
        return
    if (
        consent.consent_state == "approved"
        and detail.proposal.current_state == "AWAITING_CLIENT_CONSENT"
    ):
        raise_proposal_discussion_pack_snapshot_conflict()


__all__ = [
    "project_discussion_consent",
    "project_discussion_package",
    "validate_discussion_consent_lifecycle",
]
