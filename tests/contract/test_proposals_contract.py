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
    lineage_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/lineage"]["get"]

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
    lineage_parameters = {
        parameter["name"]: parameter for parameter in lineage_operation["parameters"]
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
    assert lineage_parameters["proposal_id"]["description"]
    assert lineage_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]


def test_proposals_openapi_write_contract() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    simulate_operation = spec["paths"]["/api/v1/proposals/simulate"]["post"]
    create_operation = spec["paths"]["/api/v1/proposals"]["post"]
    create_version_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/versions"]["post"]
    submit_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/submit"]["post"]
    approve_risk_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/approve-risk"]["post"]
    approve_compliance_operation = spec["paths"][
        "/api/v1/proposals/{proposal_id}/approve-compliance"
    ]["post"]
    consent_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/record-client-consent"][
        "post"
    ]

    simulate_parameters = {
        parameter["name"]: parameter for parameter in simulate_operation["parameters"]
    }
    create_parameters = {
        parameter["name"]: parameter for parameter in create_operation["parameters"]
    }
    create_version_parameters = {
        parameter["name"]: parameter for parameter in create_version_operation["parameters"]
    }
    submit_parameters = {
        parameter["name"]: parameter for parameter in submit_operation["parameters"]
    }
    approve_risk_parameters = {
        parameter["name"]: parameter for parameter in approve_risk_operation["parameters"]
    }
    approve_compliance_parameters = {
        parameter["name"]: parameter for parameter in approve_compliance_operation["parameters"]
    }
    consent_parameters = {
        parameter["name"]: parameter for parameter in consent_operation["parameters"]
    }

    assert "idempotency" in simulate_operation["description"].lower()
    assert simulate_parameters["Idempotency-Key"]["description"]
    assert simulate_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-simulate-1"]

    assert "idempotency" in create_operation["description"].lower()
    assert create_parameters["Idempotency-Key"]["description"]
    assert create_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-create-1"]

    assert create_version_parameters["proposal_id"]["description"]
    assert create_version_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert create_version_parameters["Idempotency-Key"]["description"]
    assert create_version_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-version-2"]

    assert submit_parameters["proposal_id"]["description"]
    assert submit_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert submit_parameters["Idempotency-Key"]["description"]
    assert submit_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-submit-1"]

    assert approve_risk_parameters["proposal_id"]["description"]
    assert approve_risk_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert approve_risk_parameters["Idempotency-Key"]["description"]
    assert approve_risk_parameters["Idempotency-Key"]["schema"]["examples"] == [
        "idem-approve-risk-1"
    ]

    assert approve_compliance_parameters["proposal_id"]["description"]
    assert approve_compliance_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert approve_compliance_parameters["Idempotency-Key"]["description"]
    assert approve_compliance_parameters["Idempotency-Key"]["schema"]["examples"] == [
        "idem-approve-compliance-1"
    ]

    assert consent_parameters["proposal_id"]["description"]
    assert consent_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert consent_parameters["Idempotency-Key"]["description"]
    assert consent_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-client-consent-1"]
