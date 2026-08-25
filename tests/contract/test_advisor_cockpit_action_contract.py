from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.contracts.advisor_cockpit_action_envelopes import (
    AdvisorCockpitActionEnvelopeResponse,
    AdvisorCockpitActionPageEnvelopeResponse,
)
from app.main import app
from tests.support.advisor_cockpit_fixtures import (
    advisor_action_item_payload,
    advisor_action_page_payload,
)


def test_advisor_cockpit_action_contract_accepts_source_owned_read_shapes() -> None:
    page_response = AdvisorCockpitActionPageEnvelopeResponse.model_validate(
        {
            "correlation_id": "corr-action-contract",
            "contract_version": "v1",
            "data": advisor_action_page_payload(),
        }
    )
    detail_response = AdvisorCockpitActionEnvelopeResponse.model_validate(
        {
            "correlation_id": "corr-action-contract",
            "contract_version": "v1",
            "data": advisor_action_item_payload(),
        }
    )

    assert page_response.data.items[0].action_family == "POLICY_REVIEW_REQUIRED"
    assert detail_response.data.evidence_refs[0].source_system == "lotus-advise"
    assert detail_response.data.acknowledgement_state.acknowledged is False


@pytest.mark.parametrize(
    ("payload_mutation", "expected_field"),
    [
        (lambda payload: payload["data"].pop("action_family"), "action_family"),
        (
            lambda payload: payload["data"].update({"gateway_posture": "INVENTED"}),
            "gateway_posture",
        ),
        (lambda payload: payload["data"].update({"action_item_version": 0}), "action_item_version"),
    ],
)
def test_advisor_cockpit_action_contract_rejects_malformed_or_invented_shapes(
    payload_mutation,
    expected_field: str,
) -> None:
    payload = {
        "correlation_id": "corr-invalid-action-contract",
        "data": advisor_action_item_payload(),
    }
    payload_mutation(payload)

    with pytest.raises(ValidationError) as exc:
        AdvisorCockpitActionEnvelopeResponse.model_validate(payload)

    assert expected_field in str(exc.value)


def test_advisor_cockpit_action_contract_rejects_nested_unknown_fields() -> None:
    payload = advisor_action_item_payload()
    payload["evidence_refs"][0]["raw_provider_payload"] = {"secret": "must-not-pass"}

    with pytest.raises(ValidationError, match="raw_provider_payload"):
        AdvisorCockpitActionEnvelopeResponse(
            correlation_id="corr-invalid-nested-action",
            data=payload,
        )


def test_advisor_cockpit_action_openapi_uses_typed_non_free_form_schemas() -> None:
    schemas = TestClient(app).get("/openapi.json").json()["components"]["schemas"]
    list_schema = schemas["AdvisorCockpitActionPageEnvelopeResponse"]
    detail_schema = schemas["AdvisorCockpitActionEnvelopeResponse"]

    assert (
        list_schema["properties"]["data"]["$ref"] == "#/components/schemas/AdvisorCockpitActionPage"
    )
    assert (
        detail_schema["properties"]["data"]["$ref"]
        == "#/components/schemas/AdvisorCockpitActionItem"
    )
    assert schemas["AdvisorCockpitActionPage"]["additionalProperties"] is False
    assert schemas["AdvisorCockpitActionItem"]["additionalProperties"] is False
    assert schemas["AdvisorCockpitActionEvidenceRef"]["additionalProperties"] is False
    assert "supportability" not in schemas["AdvisorCockpitActionItem"]["properties"]
    assert "gateway_posture" not in schemas["AdvisorCockpitActionItem"]["properties"]
    assert list_schema["examples"][0]["data"]["items"][0]["action_family"] == (
        "POLICY_REVIEW_REQUIRED"
    )
    assert detail_schema["examples"][0]["data"]["unsupported_capabilities"] == [
        "CLIENT_READY_PUBLICATION"
    ]


def test_advisor_cockpit_action_page_has_a_bounded_item_collection() -> None:
    payload = advisor_action_page_payload()
    payload["items"] = [deepcopy(payload["items"][0]) for _ in range(65)]

    with pytest.raises(ValidationError, match="items"):
        AdvisorCockpitActionPageEnvelopeResponse(
            correlation_id="corr-too-many-actions",
            data=payload,
        )
