from typing import Any

from app.contracts.proposal_discussion_pack import (
    ProposalDiscussionClientReleaseBoundary,
    ProposalDiscussionLineage,
    ProposalDiscussionMemoEvidence,
    ProposalDiscussionNarrativeEvidence,
    ProposalDiscussionOverallState,
    ProposalDiscussionPackageEvidence,
    ProposalDiscussionPackData,
)
from app.services.proposal_discussion_pack_capabilities import (
    proposal_discussion_pack_capabilities,
)
from app.services.proposal_discussion_pack_source_contract import SourceDiscussionDetail
from app.services.proposal_discussion_pack_source_projection import (
    ProposalDiscussionSourceResponse,
    project_discussion_memo,
    project_discussion_narrative,
)
from app.services.proposal_discussion_pack_source_validation import (
    validated_discussion_detail,
)
from app.services.proposal_discussion_pack_workflow_projection import (
    project_discussion_consent,
    project_discussion_package,
    validate_discussion_consent_lifecycle,
)


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
    detail = _validated_detail(
        detail_payload,
        expected_proposal_id=expected_proposal_id,
        expected_portfolio_id=expected_portfolio_id,
        expected_version_no=expected_version_no,
    )
    narrative = project_discussion_narrative(narrative_response, detail)
    memo = project_discussion_memo(memo_response, detail)
    package = project_discussion_package(delivery_response, detail)
    consent = project_discussion_consent(approvals_response, detail)
    validate_discussion_consent_lifecycle(consent, detail)
    return ProposalDiscussionPackData(
        proposal_id=detail.proposal.proposal_id,
        portfolio_id=detail.proposal.portfolio_id,
        title=detail.proposal.title,
        current_state=detail.proposal.current_state,
        version_no=detail.current_version.version_no,
        version_created_at=detail.current_version.created_at,
        overall_state=_overall_state(narrative, memo, package, consent),
        attention_required=_attention_required(narrative, memo, package, consent),
        narrative=narrative,
        memo=memo,
        package=package,
        consent=consent,
        client_release=_client_release_boundary(),
        capabilities=proposal_discussion_pack_capabilities(narrative, memo, package, consent),
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


def _validated_detail(
    payload: dict[str, Any],
    *,
    expected_proposal_id: str,
    expected_portfolio_id: str,
    expected_version_no: int,
) -> SourceDiscussionDetail:
    return validated_discussion_detail(
        payload,
        expected_proposal_id=expected_proposal_id,
        expected_portfolio_id=expected_portfolio_id,
        expected_version_no=expected_version_no,
    )


def _overall_state(*evidence: object) -> ProposalDiscussionOverallState:
    supported_states = {"supported", "not_available", "not_supported"}
    return (
        "supported"
        if all(getattr(item, "state", None) in supported_states for item in evidence)
        else "partial"
    )


def _attention_required(
    narrative: ProposalDiscussionNarrativeEvidence,
    memo: ProposalDiscussionMemoEvidence,
    package: ProposalDiscussionPackageEvidence,
    consent: object,
) -> bool:
    return (
        _overall_state(narrative, memo, package, consent) == "partial"
        or narrative.status is not None
        and narrative.status != "READY_FOR_ADVISOR_REVIEW"
        or memo.memo_status is not None
        and memo.memo_status != "READY"
        or package.package_state == "attention"
    )


def _client_release_boundary() -> ProposalDiscussionClientReleaseBoundary:
    return ProposalDiscussionClientReleaseBoundary(
        state="blocked",
        reason_code="client_release_not_supported",
        publication_supported=False,
        delivery_supported=False,
        explanation=(
            "Advisor-use narrative, memo, and report evidence is not client-release, "
            "publication, communication, or delivery authority."
        ),
    )


__all__ = [
    "ProposalDiscussionSourceResponse",
    "project_proposal_discussion_pack",
]
