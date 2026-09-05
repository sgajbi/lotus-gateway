"""Caller-supplied datetime fields refuse Unix-timestamp numbers locally, so a
value the caller never wrote is never re-serialized toward Lotus Idea."""

import pytest
from pydantic import ValidationError

from app.contracts.idea_actions import (
    IdeaCandidateConversionIntentRequest,
    IdeaCandidateReviewActionRequest,
)
from app.contracts.idea_interactions import (
    IdeaCandidateFeedbackRequest,
    IdeaPresentationReceiptFields,
)

_REVIEW_BASE = {
    "action": "approve_for_conversion",
    "reviewId": "review-001",
    "reasonCodes": ["high_cash_ratio"],
    "decidedAtUtc": "2026-04-10T02:00:00+00:00",
}


def test_review_action_refuses_numeric_decided_at() -> None:
    with pytest.raises(ValidationError) as raised:
        IdeaCandidateReviewActionRequest.model_validate(
            {**_REVIEW_BASE, "decidedAtUtc": 1782036720}
        )
    assert "ISO-8601 date-time string" in str(raised.value)


def test_review_action_refuses_numeric_snoozed_until() -> None:
    with pytest.raises(ValidationError) as raised:
        IdeaCandidateReviewActionRequest.model_validate(
            {**_REVIEW_BASE, "snoozedUntilUtc": 1782036720.5}
        )
    assert "ISO-8601 date-time string" in str(raised.value)


def test_conversion_intent_refuses_numeric_requested_at() -> None:
    with pytest.raises(ValidationError) as raised:
        IdeaCandidateConversionIntentRequest.model_validate(
            {
                "conversionIntentId": "conversion-001",
                "reasonCodes": ["high_cash_ratio"],
                "requestedAtUtc": 1782036720,
            }
        )
    assert "ISO-8601 date-time string" in str(raised.value)


def test_feedback_refuses_numeric_recorded_at() -> None:
    with pytest.raises(ValidationError) as raised:
        IdeaCandidateFeedbackRequest.model_validate(
            {
                "feedbackId": "feedback-001",
                "taxonomyVersion": "idea-feedback-taxonomy-v1",
                "outcome": "useful",
                "reason": "relevant",
                "recordedAtUtc": 1782036720,
            }
        )
    assert "ISO-8601 date-time string" in str(raised.value)


def test_presentation_receipt_refuses_numeric_presented_at() -> None:
    with pytest.raises(ValidationError) as raised:
        IdeaPresentationReceiptFields.model_validate(
            {
                "presentedAtUtc": 1782036720,
                "rankAtPresentation": 1,
                "visibleCandidateCount": 10,
                "queueSnapshotDigest": "sha256:" + "0" * 64,
                "queuePolicyVersion": "policy-v1",
                "rankingPolicyVersion": "ranking-v1",
                "candidateMaterialVersion": 1,
                "candidateEvidenceVersion": 1,
            }
        )
    assert "ISO-8601 date-time string" in str(raised.value)


def test_iso_strings_still_parse_with_timezone_validation() -> None:
    request = IdeaCandidateReviewActionRequest.model_validate(_REVIEW_BASE)
    assert request.decided_at_utc.utcoffset() is not None


@pytest.mark.parametrize(
    "value",
    [1782036720, 1782036720.5, "1782036720", " 1782036720.5 ", "-1782036720"],
)
def test_numeric_shapes_are_refused_in_both_json_types(value) -> None:
    with pytest.raises(ValidationError) as raised:
        IdeaCandidateReviewActionRequest.model_validate({**_REVIEW_BASE, "decidedAtUtc": value})
    assert "ISO-8601 date-time string" in str(raised.value)
