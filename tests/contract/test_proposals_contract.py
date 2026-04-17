from fastapi.testclient import TestClient

from app.contracts.proposals import (
    ProposalApprovalActionRequest,
    ProposalEnvelopeResponse,
    ProposalSimulateResponse,
    ProposalSubmitRequest,
)
from app.main import app


def test_proposals_contract_shape() -> None:
    payload = ProposalSimulateResponse(
        correlation_id="corr_1",
        contract_version="v1",
        data={"status": "READY", "proposal_run_id": "pr_1"},
    )
    assert payload.data["status"] == "READY"


def test_proposal_envelope_contract_shape() -> None:
    payload = ProposalEnvelopeResponse(
        correlation_id="corr_2",
        contract_version="v1",
        data={"items": [{"proposal_id": "pp_1", "current_state": "DRAFT"}]},
    )
    assert payload.data["items"][0]["proposal_id"] == "pp_1"


def test_proposal_submit_request_contract_shape() -> None:
    payload = ProposalSubmitRequest(actor_id="advisor_1")
    assert payload.review_type == "RISK"
    assert payload.expected_state == "DRAFT"


def test_proposal_approval_action_request_contract_shape() -> None:
    payload = ProposalApprovalActionRequest(actor_id="risk_1", expected_state="RISK_REVIEW")
    assert payload.related_version_no is None
    assert payload.details == {}


def test_proposals_openapi_read_contract() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    list_operation = spec["paths"]["/api/v1/proposals"]["get"]
    detail_operation = spec["paths"]["/api/v1/proposals/{proposal_id}"]["get"]
    version_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/versions/{version_no}"][
        "get"
    ]
    events_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/workflow-events"]["get"]
    approvals_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/approvals"]["get"]

    list_parameters = {parameter["name"]: parameter for parameter in list_operation["parameters"]}
    detail_parameters = {
        parameter["name"]: parameter for parameter in detail_operation["parameters"]
    }
    version_parameters = {
        parameter["name"]: parameter for parameter in version_operation["parameters"]
    }
    events_parameters = {
        parameter["name"]: parameter for parameter in events_operation["parameters"]
    }
    approvals_parameters = {
        parameter["name"]: parameter for parameter in approvals_operation["parameters"]
    }

    assert "portfolio" in list_operation["description"].lower()
    assert list_parameters["portfolio_id"]["description"]
    assert list_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert list_parameters["state"]["description"]
    assert list_parameters["state"]["schema"]["examples"] == ["DRAFT"]
    assert list_parameters["created_by"]["description"]
    assert list_parameters["created_by"]["schema"]["examples"] == ["advisor_1"]
    assert list_parameters["created_from"]["description"]
    assert list_parameters["created_from"]["schema"]["examples"] == ["2026-01-01"]
    assert list_parameters["created_to"]["description"]
    assert list_parameters["created_to"]["schema"]["examples"] == ["2026-03-31"]
    assert list_parameters["limit"]["description"]
    assert list_parameters["limit"]["schema"]["default"] == 20
    assert list_parameters["cursor"]["description"]
    assert list_parameters["cursor"]["schema"]["examples"] == ["pp_00042"]

    assert detail_parameters["proposal_id"]["description"]
    assert detail_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert detail_parameters["include_evidence"]["description"]
    assert detail_parameters["include_evidence"]["schema"]["default"] is False
    assert detail_parameters["include_evidence"]["schema"]["examples"] == [True]

    assert version_parameters["proposal_id"]["description"]
    assert version_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert version_parameters["version_no"]["description"]
    assert version_parameters["version_no"]["schema"]["examples"] == [2]
    assert version_parameters["include_evidence"]["description"]
    assert version_parameters["include_evidence"]["schema"]["default"] is False

    assert events_parameters["proposal_id"]["description"]
    assert events_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert approvals_parameters["proposal_id"]["description"]
    assert approvals_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
