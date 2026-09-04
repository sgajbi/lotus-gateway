"""The action-evidence binding table must stay coherent with the contracts it names.

These assertions turn silent runtime drift (a renamed evidence field, a request field the
evidence model cannot echo, a new action missing its binding) into a CI failure instead of a
production 502 that blames Lotus Idea.
"""

import asyncio
from typing import get_args

import pytest
from fastapi import HTTPException

from app.contracts.idea_actions import IdeaCandidateReviewActionRequest
from app.contracts.ideas import IdeaReasonCode
from app.services.idea_service import (
    _ACTION_EVIDENCE_BINDINGS,
    IdeaCandidateActionMethod,
    IdeaService,
)


def _review_request(**overrides) -> IdeaCandidateReviewActionRequest:
    payload = {
        "reviewId": "review-001",
        "action": "approve_for_conversion",
        "reasonCodes": ("review_required",),
        "decidedAtUtc": "2026-06-21T10:15:00Z",
        **overrides,
    }
    return IdeaCandidateReviewActionRequest.model_validate(payload)


def test_bindings_cover_every_candidate_action_method() -> None:
    assert set(_ACTION_EVIDENCE_BINDINGS) == set(get_args(IdeaCandidateActionMethod))


@pytest.mark.parametrize(
    ("action", "binding"),
    _ACTION_EVIDENCE_BINDINGS.items(),
    ids=list(_ACTION_EVIDENCE_BINDINGS),
)
def test_evidence_model_echoes_every_request_field(action, binding) -> None:
    evidence_model = binding.response_type.model_fields[binding.evidence_field].annotation
    request_fields = set(binding.request_type.model_fields)
    evidence_fields = set(evidence_model.model_fields)

    assert request_fields <= evidence_fields, (
        f"{action}: evidence model {evidence_model.__name__} cannot echo "
        f"{sorted(request_fields - evidence_fields)}"
    )
    assert "candidate_id" in evidence_fields


def test_review_expected_evidence_places_owned_reason_first_exactly_once() -> None:
    expected = _review_request().expected_evidence_fields()
    assert expected["reason_codes"] == (
        IdeaReasonCode.REVIEW_APPROVED_FOR_CONVERSION,
        IdeaReasonCode.REVIEW_REQUIRED,
    )

    already_included = _review_request(
        reasonCodes=("review_required", "review_approved_for_conversion")
    ).expected_evidence_fields()
    assert already_included["reason_codes"] == (
        IdeaReasonCode.REVIEW_APPROVED_FOR_CONVERSION,
        IdeaReasonCode.REVIEW_REQUIRED,
    )

    escalated = _review_request(
        action="escalate_to_compliance", reasonCodes=("concentration_attention",)
    ).expected_evidence_fields()
    assert escalated["reason_codes"] == (
        IdeaReasonCode.REVIEW_ESCALATED,
        IdeaReasonCode.CONCENTRATION_ATTENTION,
    )


def test_mispaired_action_and_request_fail_before_the_source_is_called() -> None:
    class _RefusingClient:
        def __getattr__(self, name: str):
            raise AssertionError("Gateway must reject a mispaired action before calling Idea.")

    service = IdeaService(idea_client=_RefusingClient())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            service.record_candidate_action(
                action="record_candidate_feedback",
                candidate_id="idea_high_cash_8d57adbf52f7f5a7",
                request=_review_request(),
                caller_headers={},
                correlation_id="corr-binding-guard",
                idempotency_key="idem-binding-guard",
                causation_id=None,
            )
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["code"] == "idea_contract_invalid"
