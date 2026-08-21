from dataclasses import dataclass
from typing import Any

from app.contracts.proposal_discussion_pack import (
    ProposalDiscussionCapability,
    ProposalDiscussionCapabilityState,
    ProposalDiscussionClientReleaseBoundary,
    ProposalDiscussionConsentEvidence,
    ProposalDiscussionDisclosure,
    ProposalDiscussionLimitation,
    ProposalDiscussionLineage,
    ProposalDiscussionMemoEvidence,
    ProposalDiscussionMemoSection,
    ProposalDiscussionNarrativeEvidence,
    ProposalDiscussionNarrativeSection,
    ProposalDiscussionNarrativeSourceRef,
    ProposalDiscussionOverallState,
    ProposalDiscussionPackageEvidence,
    ProposalDiscussionPackageState,
    ProposalDiscussionPackData,
)
from app.services.proposal_discussion_pack_errors import (
    raise_proposal_discussion_pack_contract_invalid,
)
from app.services.proposal_discussion_pack_source_contract import (
    SourceDiscussionApprovals,
    SourceDiscussionDelivery,
    SourceDiscussionDetail,
    SourceDiscussionMemo,
    SourceDiscussionNarrative,
)
from app.services.proposal_discussion_pack_source_validation import (
    validated_discussion_approvals,
    validated_discussion_delivery,
    validated_discussion_detail,
    validated_discussion_memo,
    validated_discussion_narrative,
)


@dataclass(frozen=True)
class ProposalDiscussionSourceResponse:
    status_code: int
    payload: dict[str, Any]


@dataclass(frozen=True)
class _SourceEvidence:
    state: ProposalDiscussionCapabilityState
    reason_code: str


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


def project_proposal_discussion_pack(
    *,
    detail_payload: dict[str, Any],
    narrative_response: ProposalDiscussionSourceResponse,
    memo_response: ProposalDiscussionSourceResponse,
    approvals_response: ProposalDiscussionSourceResponse,
    delivery_response: ProposalDiscussionSourceResponse,
    expected_proposal_id: str,
    expected_portfolio_id: str,
    expected_version_no: int,
    correlation_id: str,
) -> ProposalDiscussionPackData:
    """Compose selected-record evidence without inventing a client-readiness decision."""

    detail = validated_discussion_detail(
        detail_payload,
        expected_proposal_id=expected_proposal_id,
        expected_portfolio_id=expected_portfolio_id,
        expected_version_no=expected_version_no,
    )
    narrative_source, narrative_evidence = _narrative_source(narrative_response, detail)
    memo_source, memo_evidence = _memo_source(memo_response, detail)
    approvals_source, approvals_evidence = _approvals_source(approvals_response, detail)
    delivery_source, delivery_evidence = _delivery_source(delivery_response, detail)

    narrative = _narrative(narrative_source, narrative_evidence)
    memo = _memo(memo_source, memo_evidence)
    package = _package(delivery_source, delivery_evidence, detail)
    consent = _consent(approvals_source, approvals_evidence, detail)
    _validate_consent_lifecycle(consent, detail)
    capabilities = _capabilities(
        narrative=narrative,
        memo=memo,
        package=package,
        consent=consent,
    )
    overall_state: ProposalDiscussionOverallState = (
        "supported"
        if all(
            evidence.state in {"supported", "not_available", "not_supported"}
            for evidence in (narrative, memo, package, consent)
        )
        else "partial"
    )
    return ProposalDiscussionPackData(
        proposal_id=detail.proposal.proposal_id,
        portfolio_id=detail.proposal.portfolio_id,
        title=detail.proposal.title,
        current_state=detail.proposal.current_state,
        version_no=detail.current_version.version_no,
        version_created_at=detail.current_version.created_at,
        overall_state=overall_state,
        attention_required=(
            overall_state == "partial"
            or narrative.status is not None
            and narrative.status != "READY_FOR_ADVISOR_REVIEW"
            or memo.memo_status is not None
            and memo.memo_status != "READY"
            or package.package_state == "attention"
        ),
        narrative=narrative,
        memo=memo,
        package=package,
        consent=consent,
        client_release=ProposalDiscussionClientReleaseBoundary(
            state="blocked",
            reason_code="client_release_not_supported",
            publication_supported=False,
            delivery_supported=False,
            explanation=(
                "Advisor-use narrative, memo, and report evidence is not client-release, "
                "publication, communication, or delivery authority."
            ),
        ),
        capabilities=capabilities,
        lineage=ProposalDiscussionLineage(
            proposal_version_id=detail.current_version.proposal_version_id,
            request_hash=detail.current_version.request_hash,
            artifact_hash=detail.current_version.artifact_hash,
            simulation_hash=detail.current_version.simulation_hash,
            narrative_hash=narrative.source_narrative_hash,
            memo_hash=memo.memo_hash,
            gateway_correlation_id=correlation_id,
        ),
    )


def _narrative_source(
    response: ProposalDiscussionSourceResponse,
    detail: SourceDiscussionDetail,
) -> tuple[SourceDiscussionNarrative | None, _SourceEvidence]:
    evidence = _source_evidence(response, capability="advisor_narrative")
    if evidence.state != "supported":
        return None, evidence
    return validated_discussion_narrative(response.payload, detail=detail), evidence


def _memo_source(
    response: ProposalDiscussionSourceResponse,
    detail: SourceDiscussionDetail,
) -> tuple[SourceDiscussionMemo | None, _SourceEvidence]:
    evidence = _source_evidence(response, capability="advisor_memo")
    if evidence.state != "supported":
        return None, evidence
    return validated_discussion_memo(response.payload, detail=detail), evidence


def _approvals_source(
    response: ProposalDiscussionSourceResponse,
    detail: SourceDiscussionDetail,
) -> tuple[SourceDiscussionApprovals | None, _SourceEvidence]:
    evidence = _source_evidence(response, capability="approval_and_consent_records")
    if evidence.state != "supported":
        return None, evidence
    return validated_discussion_approvals(response.payload, detail=detail), evidence


def _delivery_source(
    response: ProposalDiscussionSourceResponse,
    detail: SourceDiscussionDetail,
) -> tuple[SourceDiscussionDelivery | None, _SourceEvidence]:
    evidence = _source_evidence(response, capability="report_package")
    if evidence.state != "supported":
        return None, evidence
    return validated_discussion_delivery(response.payload, detail=detail), evidence


def _source_evidence(
    response: ProposalDiscussionSourceResponse,
    *,
    capability: str,
) -> _SourceEvidence:
    if response.status_code < 400:
        return _SourceEvidence("supported", f"{capability}_source_available")
    if response.status_code == 403:
        return _SourceEvidence("restricted", f"{capability}_source_restricted")
    if response.status_code == 404:
        return _SourceEvidence("not_available", f"{capability}_not_recorded")
    return _SourceEvidence("unavailable", f"{capability}_source_unavailable")


def _narrative(
    source: SourceDiscussionNarrative | None,
    evidence: _SourceEvidence,
) -> ProposalDiscussionNarrativeEvidence:
    if source is None:
        return ProposalDiscussionNarrativeEvidence(
            state=evidence.state,
            reason_code=evidence.reason_code,
        )
    narrative = source.proposal_narrative
    review = source.narrative_review
    return ProposalDiscussionNarrativeEvidence(
        state="supported",
        reason_code="advisor_narrative_available",
        narrative_id=narrative.narrative_id,
        source_narrative_hash=source.source_narrative_hash,
        status=narrative.status,
        generation_mode=narrative.generation_mode,
        review_state="DRAFT" if review is None else review.review_state,
        review_id=None if review is None else review.review_id,
        reviewed_by=None if review is None else review.reviewed_by,
        reviewed_at=None if review is None else review.reviewed_at,
        client_ready_status=(
            "BLOCKED_REVIEW_REQUIRED" if review is None else review.client_ready_status
        ),
        policy_status=narrative.narrative_policy.status,
        policy_version=narrative.narrative_policy.policy_version,
        sections=[
            ProposalDiscussionNarrativeSection(
                section_key=section.section_key,
                title=section.title,
                text=section.text,
                source_refs=[
                    ProposalDiscussionNarrativeSourceRef.model_validate(item.model_dump())
                    for item in section.source_refs
                ],
                limitation_refs=section.limitation_refs,
            )
            for section in narrative.sections
        ],
        disclosures=[
            ProposalDiscussionDisclosure.model_validate(item.model_dump())
            for item in narrative.disclosures
        ],
        client_ready_blockers=narrative.narrative_policy.client_ready_blockers,
        limitations=[
            ProposalDiscussionLimitation.model_validate(item.model_dump())
            for item in narrative.limitations
        ],
    )


def _memo(
    source: SourceDiscussionMemo | None,
    evidence: _SourceEvidence,
) -> ProposalDiscussionMemoEvidence:
    if source is None:
        return ProposalDiscussionMemoEvidence(
            state=evidence.state,
            reason_code=evidence.reason_code,
        )
    review = source.review_posture
    return ProposalDiscussionMemoEvidence(
        state="supported",
        reason_code="advisor_memo_available",
        memo_id=source.memo_id,
        memo_version=source.memo_version,
        memo_status=source.memo_status,
        lifecycle_status=source.lifecycle_status,
        source_input_hash=source.source_input_hash,
        memo_hash=source.memo_hash,
        latest_review_action=review.review_action,
        review_event_id=review.event_id,
        reviewed_by=review.actor_id,
        reviewed_at=review.occurred_at,
        client_ready_publication="BLOCKED",
        sections=[
            ProposalDiscussionMemoSection.model_validate(section.model_dump())
            for section in source.memo.sections
        ],
    )


def _package(
    source: SourceDiscussionDelivery | None,
    evidence: _SourceEvidence,
    detail: SourceDiscussionDetail,
) -> ProposalDiscussionPackageEvidence:
    if source is None:
        return ProposalDiscussionPackageEvidence(
            state=evidence.state,
            reason_code=evidence.reason_code,
            package_state="not_requested",
        )
    reporting = source.reporting
    if reporting is None:
        return ProposalDiscussionPackageEvidence(
            state="not_available",
            reason_code="report_package_not_requested",
            package_state="not_requested",
        )
    normalized_status = reporting.status.upper()
    if normalized_status in _AVAILABLE_REPORT_STATUSES:
        package_state: ProposalDiscussionPackageState = "available"
        reason_code = "report_package_available"
    elif normalized_status in _PENDING_REPORT_STATUSES:
        package_state = "pending"
        reason_code = "report_package_pending"
    elif normalized_status in _ATTENTION_REPORT_STATUSES:
        package_state = "attention"
        reason_code = "report_package_requires_attention"
    else:
        raise_proposal_discussion_pack_contract_invalid()
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


def _consent(
    source: SourceDiscussionApprovals | None,
    evidence: _SourceEvidence,
    detail: SourceDiscussionDetail,
) -> ProposalDiscussionConsentEvidence:
    if source is None:
        return ProposalDiscussionConsentEvidence(
            state=evidence.state,
            reason_code=evidence.reason_code,
            consent_state="not_recorded",
        )
    current = [
        item
        for item in source.approvals
        if item.approval_type == "CLIENT_CONSENT"
        and item.related_version_no == detail.current_version.version_no
    ]
    if not current:
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
    latest = current[-1]
    return ProposalDiscussionConsentEvidence(
        state="supported",
        reason_code="client_consent_recorded" if latest.approved else "client_consent_declined",
        consent_state="approved" if latest.approved else "declined",
        approval_id=latest.approval_id,
        actor_id=latest.actor_id,
        occurred_at=latest.occurred_at,
        related_version_no=latest.related_version_no,
    )


def _validate_consent_lifecycle(
    consent: ProposalDiscussionConsentEvidence,
    detail: SourceDiscussionDetail,
) -> None:
    if consent.state != "supported":
        return
    if (
        consent.consent_state == "approved"
        and detail.proposal.current_state == "AWAITING_CLIENT_CONSENT"
    ):
        raise_proposal_discussion_pack_contract_invalid()
    if consent.consent_state == "not_recorded" and detail.proposal.current_state in {
        "EXECUTION_READY",
        "EXECUTED",
    }:
        raise_proposal_discussion_pack_contract_invalid()


def _capabilities(
    *,
    narrative: ProposalDiscussionNarrativeEvidence,
    memo: ProposalDiscussionMemoEvidence,
    package: ProposalDiscussionPackageEvidence,
    consent: ProposalDiscussionConsentEvidence,
) -> list[ProposalDiscussionCapability]:
    return [
        ProposalDiscussionCapability(
            key="proposal_identity",
            state="supported",
            reason_code="request_bound_proposal_version_available",
            source_service="lotus-advise",
            support_reference="ProposalDetailResponse",
        ),
        ProposalDiscussionCapability(
            key="advisor_narrative",
            state=narrative.state,
            reason_code=narrative.reason_code,
            source_service="lotus-advise" if narrative.state == "supported" else None,
            support_reference="ProposalNarrativeReadResponse",
        ),
        ProposalDiscussionCapability(
            key="advisor_memo",
            state=memo.state,
            reason_code=memo.reason_code,
            source_service="lotus-advise" if memo.state == "supported" else None,
            support_reference="ProposalMemoResponse",
        ),
        ProposalDiscussionCapability(
            key="disclosure_policy",
            state=narrative.state,
            reason_code=(
                "narrative_disclosure_policy_available"
                if narrative.state == "supported"
                else narrative.reason_code
            ),
            source_service="lotus-advise" if narrative.state == "supported" else None,
            support_reference="ProposalNarrativePolicy.required_disclosures",
        ),
        ProposalDiscussionCapability(
            key="report_package",
            state=package.state,
            reason_code=package.reason_code,
            source_service=("lotus-report" if package.state in {"supported", "partial"} else None),
            support_reference="ProposalDeliverySummaryResponse.reporting",
        ),
        ProposalDiscussionCapability(
            key="approval_and_consent_records",
            state=consent.state,
            reason_code=consent.reason_code,
            source_service="lotus-advise" if consent.state in {"supported", "partial"} else None,
            support_reference="ProposalApprovalsResponse.approvals",
        ),
        ProposalDiscussionCapability(
            key="client_release",
            state="not_supported",
            reason_code="client_release_authority_not_exposed",
            support_reference="RFC-0023/RFC-0024 boundary",
        ),
        ProposalDiscussionCapability(
            key="client_delivery",
            state="not_supported",
            reason_code="client_communication_delivery_not_supported",
        ),
    ]


__all__ = [
    "ProposalDiscussionSourceResponse",
    "project_proposal_discussion_pack",
]
