from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.services.proposal_discussion_pack_errors import (
    raise_proposal_discussion_pack_contract_invalid,
)
from app.services.proposal_discussion_pack_source_contract import (
    SourceDiscussionApprovals,
    SourceDiscussionDelivery,
    SourceDiscussionDetail,
    SourceDiscussionMemo,
    SourceDiscussionNarrative,
    SourceDiscussionProposal,
    SourceMemoEventPosture,
)

SourceModelT = TypeVar("SourceModelT", bound=BaseModel)


def validated_discussion_detail(
    payload: dict[str, object],
    *,
    expected_proposal_id: str,
    expected_portfolio_id: str,
    expected_version_no: int,
) -> SourceDiscussionDetail:
    source = _validate(SourceDiscussionDetail, payload)
    _validate_proposal_identity(
        source.proposal,
        expected_proposal_id=expected_proposal_id,
        expected_portfolio_id=expected_portfolio_id,
        expected_version_no=expected_version_no,
    )
    version = source.current_version
    if (
        version.proposal_id != expected_proposal_id
        or version.version_no != expected_version_no
        or source.proposal.current_version_no != version.version_no
        or version.created_at < source.proposal.created_at
        or source.proposal.last_event_at < version.created_at
    ):
        raise_proposal_discussion_pack_contract_invalid()
    return source


def validated_discussion_narrative(
    payload: dict[str, object],
    *,
    detail: SourceDiscussionDetail,
) -> SourceDiscussionNarrative:
    source = _validate(SourceDiscussionNarrative, payload)
    _validate_child_identity(
        source.proposal,
        proposal_id=detail.proposal.proposal_id,
        portfolio_id=detail.proposal.portfolio_id,
        version_no=detail.current_version.version_no,
    )
    narrative = source.proposal_narrative
    review = source.narrative_review
    if (
        source.proposal_version_no != detail.current_version.version_no
        or source.proposal_version_id != detail.current_version.proposal_version_id
        or review is not None
        and (
            review.proposal_id != detail.proposal.proposal_id
            or review.proposal_version_no != detail.current_version.version_no
            or review.narrative_id != narrative.narrative_id
            or review.source_narrative_hash != source.source_narrative_hash
            or review.reviewed_at < detail.current_version.created_at
        )
    ):
        raise_proposal_discussion_pack_contract_invalid()
    disclosure_ids = [item.disclosure_id for item in narrative.disclosures]
    required_ids = [item.disclosure_id for item in narrative.narrative_policy.required_disclosures]
    if len(disclosure_ids) != len(set(disclosure_ids)) or disclosure_ids != required_ids:
        raise_proposal_discussion_pack_contract_invalid()
    return source


def validated_discussion_memo(
    payload: dict[str, object],
    *,
    detail: SourceDiscussionDetail,
) -> SourceDiscussionMemo:
    source = _validate(SourceDiscussionMemo, payload)
    _validate_child_identity(
        source.proposal,
        proposal_id=detail.proposal.proposal_id,
        portfolio_id=detail.proposal.portfolio_id,
        version_no=detail.current_version.version_no,
    )
    if (
        source.proposal_version_no != detail.current_version.version_no
        or source.proposal_version_id != detail.current_version.proposal_version_id
        or source.memo.proposal_id != detail.proposal.proposal_id
        or source.memo.proposal_version_no != detail.current_version.version_no
        or source.memo.status != source.memo_status
        or source.projection.get("client_ready_publication") != "BLOCKED"
    ):
        raise_proposal_discussion_pack_contract_invalid()
    _validate_event_posture(source.review_posture)
    _validate_event_posture(source.report_package_posture)
    return source


def validated_discussion_approvals(
    payload: dict[str, object],
    *,
    detail: SourceDiscussionDetail,
) -> SourceDiscussionApprovals:
    source = _validate(SourceDiscussionApprovals, payload)
    _validate_child_identity(
        source.proposal,
        proposal_id=detail.proposal.proposal_id,
        portfolio_id=detail.proposal.portfolio_id,
        version_no=detail.current_version.version_no,
    )
    identifiers = [item.approval_id for item in source.approvals]
    if source.approval_count != len(source.approvals) or len(identifiers) != len(set(identifiers)):
        raise_proposal_discussion_pack_contract_invalid()
    if any(
        item.proposal_id != detail.proposal.proposal_id
        or item.related_version_no is not None
        and item.related_version_no > detail.current_version.version_no
        for item in source.approvals
    ):
        raise_proposal_discussion_pack_contract_invalid()
    if any(
        item.related_version_no == detail.current_version.version_no
        and item.occurred_at < detail.current_version.created_at
        for item in source.approvals
    ):
        raise_proposal_discussion_pack_contract_invalid()
    if source.approvals and source.latest_approval_at != source.approvals[-1].occurred_at:
        raise_proposal_discussion_pack_contract_invalid()
    return source


def validated_discussion_delivery(
    payload: dict[str, object],
    *,
    detail: SourceDiscussionDetail,
) -> SourceDiscussionDelivery:
    source = _validate(SourceDiscussionDelivery, payload)
    _validate_child_identity(
        source.proposal,
        proposal_id=detail.proposal.proposal_id,
        portfolio_id=detail.proposal.portfolio_id,
        version_no=detail.current_version.version_no,
    )
    if (
        source.reporting is not None
        and source.reporting.related_version_no is not None
        and source.reporting.related_version_no > detail.current_version.version_no
    ):
        raise_proposal_discussion_pack_contract_invalid()
    return source


def _validate(model: type[SourceModelT], payload: dict[str, object]) -> SourceModelT:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise_proposal_discussion_pack_contract_invalid(exc)


def _validate_proposal_identity(
    proposal: SourceDiscussionProposal,
    *,
    expected_proposal_id: str,
    expected_portfolio_id: str,
    expected_version_no: int,
) -> None:
    if (
        proposal.proposal_id != expected_proposal_id
        or proposal.portfolio_id != expected_portfolio_id
        or proposal.current_version_no != expected_version_no
    ):
        raise_proposal_discussion_pack_contract_invalid()


def _validate_child_identity(
    proposal: SourceDiscussionProposal,
    *,
    proposal_id: str,
    portfolio_id: str,
    version_no: int,
) -> None:
    _validate_proposal_identity(
        proposal,
        expected_proposal_id=proposal_id,
        expected_portfolio_id=portfolio_id,
        expected_version_no=version_no,
    )


def _validate_event_posture(posture: SourceMemoEventPosture) -> None:
    if posture.status == "NOT_RECORDED" and any(
        value is not None
        for value in (
            posture.event_id,
            posture.actor_id,
            posture.occurred_at,
            posture.review_action,
            posture.report_package_status,
        )
    ):
        raise_proposal_discussion_pack_contract_invalid()
    if posture.status == "RECORDED" and not all(
        value is not None for value in (posture.event_id, posture.actor_id, posture.occurred_at)
    ):
        raise_proposal_discussion_pack_contract_invalid()


__all__ = [
    "validated_discussion_approvals",
    "validated_discussion_delivery",
    "validated_discussion_detail",
    "validated_discussion_memo",
    "validated_discussion_narrative",
]
