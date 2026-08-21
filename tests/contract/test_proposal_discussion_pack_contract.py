import pytest
from pydantic import ValidationError

from app.contracts.proposal_discussion_pack import (
    ProposalDiscussionPackEnvelopeResponse,
)
from app.main import app
from tests.shared.proposal_discussion_pack_payload import (
    build_discussion_pack_source_payloads,
)


def test_discussion_pack_openapi_contract_is_versioned_and_request_bound() -> None:
    operation = app.openapi()["paths"]["/api/v1/proposals/{proposal_id}/discussion-pack-review"][
        "get"
    ]

    assert operation["summary"] == "Get Proposal Discussion Pack Review"
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ProposalDiscussionPackEnvelopeResponse"
    }
    parameters = {(item["in"], item["name"]): item for item in operation["parameters"]}
    assert parameters[("query", "portfolio_id")]["required"] is True
    assert parameters[("query", "version_no")]["required"] is True


def test_discussion_pack_response_rejects_undeclared_client_delivery_claim() -> None:
    payload = ProposalDiscussionPackEnvelopeResponse.model_json_schema()["example"]
    payload["data"]["client_release"]["delivery_reference"] = "message_001"

    with pytest.raises(ValidationError):
        ProposalDiscussionPackEnvelopeResponse.model_validate(payload)


def test_discussion_pack_response_uses_closed_capability_states() -> None:
    schema = ProposalDiscussionPackEnvelopeResponse.model_json_schema()

    capability = schema["$defs"]["ProposalDiscussionCapability"]
    state_schema = capability["properties"]["state"]
    assert set(state_schema["enum"]) == {
        "supported",
        "partial",
        "restricted",
        "unavailable",
        "not_available",
        "not_supported",
    }


def test_source_fixture_keeps_client_release_blocked() -> None:
    payloads = build_discussion_pack_source_payloads()

    assert payloads["narrative"]["read_posture"]["client_ready_publication"] == "GATED"
    assert payloads["memo"]["projection"]["client_ready_publication"] == "BLOCKED"
