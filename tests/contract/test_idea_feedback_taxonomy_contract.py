import json
from pathlib import Path
from typing import Any

from app.contracts.idea_interactions import (
    IDEA_FEEDBACK_TAXONOMY_VERSION,
    IdeaFeedbackOutcome,
    IdeaFeedbackReason,
)
from app.main import app

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "upstream"
    / "lotus-idea-feedback-taxonomy.v1.json"
)


def _contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_gateway_feedback_enums_match_versioned_lotus_idea_taxonomy() -> None:
    contract = _contract()

    assert contract["taxonomyVersion"] == IDEA_FEEDBACK_TAXONOMY_VERSION
    assert [outcome.value for outcome in IdeaFeedbackOutcome] == contract["outcomes"]
    assert [reason.value for reason in IdeaFeedbackReason] == contract["reasons"]
    assert "reasonCodes" not in contract


def test_openapi_publishes_feedback_taxonomy_without_legacy_aliases() -> None:
    schemas = app.openapi()["components"]["schemas"]
    request = schemas["IdeaCandidateFeedbackRequest"]
    response = schemas["IdeaFeedbackEventResponse"]

    assert schemas["IdeaFeedbackOutcome"]["enum"] == _contract()["outcomes"]
    assert schemas["IdeaFeedbackReason"]["enum"] == _contract()["reasons"]
    assert request["properties"]["taxonomyVersion"]["const"] == IDEA_FEEDBACK_TAXONOMY_VERSION
    assert "reason" in request["required"]
    assert "reasonCodes" not in request["properties"]
    assert "taxonomyVersion" in response["required"]
    assert "reasonCodes" not in response["properties"]
