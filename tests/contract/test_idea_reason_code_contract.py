import json
from pathlib import Path

from app.contracts.ideas import IdeaReasonCode
from app.main import app

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "upstream"
    / "lotus-idea-reason-codes.v1.json"
)


def _contract_values() -> list[str]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["values"]


def test_gateway_reason_enum_matches_versioned_lotus_idea_contract() -> None:
    assert [reason.value for reason in IdeaReasonCode] == _contract_values()
    assert "advisor_feedback" not in _contract_values()


def test_openapi_publishes_reason_enum_for_every_idea_action_request() -> None:
    schemas = app.openapi()["components"]["schemas"]
    assert schemas["IdeaReasonCode"]["enum"] == _contract_values()

    for request_schema_name in (
        "IdeaCandidateReviewActionRequest",
        "IdeaCandidateFeedbackRequest",
        "IdeaCandidateConversionIntentRequest",
    ):
        reason_items = schemas[request_schema_name]["properties"]["reasonCodes"]["items"]
        assert reason_items == {"$ref": "#/components/schemas/IdeaReasonCode"}
