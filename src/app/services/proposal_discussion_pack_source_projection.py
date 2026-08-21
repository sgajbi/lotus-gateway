from dataclasses import dataclass
from typing import Any

from app.contracts.proposal_discussion_pack import (
    ProposalDiscussionCapabilityState,
    ProposalDiscussionDisclosure,
    ProposalDiscussionLimitation,
    ProposalDiscussionMemoEvidence,
    ProposalDiscussionMemoSection,
    ProposalDiscussionNarrativeEvidence,
    ProposalDiscussionNarrativeSection,
    ProposalDiscussionNarrativeSourceRef,
)
from app.services.proposal_discussion_pack_source_contract import (
    SourceDiscussionDetail,
    SourceDiscussionMemo,
    SourceDiscussionNarrative,
)
from app.services.proposal_discussion_pack_source_validation import (
    validated_discussion_memo,
    validated_discussion_narrative,
)


@dataclass(frozen=True)
class ProposalDiscussionSourceResponse:
    status_code: int
    payload: dict[str, Any]


@dataclass(frozen=True)
class DiscussionSourceEvidence:
    state: ProposalDiscussionCapabilityState
    reason_code: str


def discussion_source_evidence(
    response: ProposalDiscussionSourceResponse,
    *,
    capability: str,
) -> DiscussionSourceEvidence:
    if response.status_code < 400:
        return DiscussionSourceEvidence("supported", f"{capability}_source_available")
    if response.status_code == 403:
        return DiscussionSourceEvidence("restricted", f"{capability}_source_restricted")
    if response.status_code == 404:
        return DiscussionSourceEvidence("not_available", f"{capability}_not_recorded")
    return DiscussionSourceEvidence("unavailable", f"{capability}_source_unavailable")


def project_discussion_narrative(
    response: ProposalDiscussionSourceResponse,
    detail: SourceDiscussionDetail,
) -> ProposalDiscussionNarrativeEvidence:
    evidence = discussion_source_evidence(response, capability="advisor_narrative")
    if evidence.state != "supported":
        return ProposalDiscussionNarrativeEvidence(
            state=evidence.state,
            reason_code=evidence.reason_code,
        )
    source = validated_discussion_narrative(response.payload, detail=detail)
    return _available_narrative(source)


def _available_narrative(
    source: SourceDiscussionNarrative,
) -> ProposalDiscussionNarrativeEvidence:
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
        sections=_narrative_sections(source),
        disclosures=_narrative_disclosures(source),
        client_ready_blockers=narrative.narrative_policy.client_ready_blockers,
        limitations=_narrative_limitations(source),
    )


def _narrative_sections(
    source: SourceDiscussionNarrative,
) -> list[ProposalDiscussionNarrativeSection]:
    return [
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
        for section in source.proposal_narrative.sections
    ]


def _narrative_disclosures(
    source: SourceDiscussionNarrative,
) -> list[ProposalDiscussionDisclosure]:
    return [
        ProposalDiscussionDisclosure.model_validate(item.model_dump())
        for item in source.proposal_narrative.disclosures
    ]


def _narrative_limitations(
    source: SourceDiscussionNarrative,
) -> list[ProposalDiscussionLimitation]:
    return [
        ProposalDiscussionLimitation.model_validate(item.model_dump())
        for item in source.proposal_narrative.limitations
    ]


def project_discussion_memo(
    response: ProposalDiscussionSourceResponse,
    detail: SourceDiscussionDetail,
) -> ProposalDiscussionMemoEvidence:
    evidence = discussion_source_evidence(response, capability="advisor_memo")
    if evidence.state != "supported":
        return ProposalDiscussionMemoEvidence(
            state=evidence.state,
            reason_code=evidence.reason_code,
        )
    source = validated_discussion_memo(response.payload, detail=detail)
    return _available_memo(source)


def _available_memo(source: SourceDiscussionMemo) -> ProposalDiscussionMemoEvidence:
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


__all__ = [
    "DiscussionSourceEvidence",
    "ProposalDiscussionSourceResponse",
    "discussion_source_evidence",
    "project_discussion_memo",
    "project_discussion_narrative",
]
