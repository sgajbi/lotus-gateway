from fastapi.testclient import TestClient

from app.contracts.proposals import (
    ProposalApprovalActionRequest,
    ProposalApprovalsEnvelopeResponse,
    ProposalCreateEnvelopeResponse,
    ProposalDetailEnvelopeResponse,
    ProposalEnvelopeResponse,
    ProposalLineageEnvelopeResponse,
    ProposalListEnvelopeResponse,
    ProposalSimulateResponse,
    ProposalStateTransitionEnvelopeResponse,
    ProposalSubmitRequest,
    ProposalVersionEnvelopeResponse,
    ProposalWorkflowEventsEnvelopeResponse,
)
from app.main import app


def test_proposals_contract_shape() -> None:
    payload = ProposalSimulateResponse(
        correlation_id="corr_1",
        contract_version="v1",
        data={
            "proposal_run_id": "pr_1",
            "correlation_id": "corr_engine_1",
            "status": "READY",
            "before": {},
            "intents": [],
            "after_simulated": {},
            "rule_results": [],
            "explanation": {},
            "diagnostics": {},
            "lineage": {},
        },
    )
    assert payload.data.status == "READY"


def test_proposal_read_envelope_contract_shapes() -> None:
    list_payload = ProposalListEnvelopeResponse(
        correlation_id="corr_2",
        contract_version="v1",
        data={
            "items": [{"proposal_id": "pp_1", "portfolio_id": "PF_1001", "current_state": "DRAFT"}]
        },
    )
    detail_payload = ProposalDetailEnvelopeResponse(
        correlation_id="corr_3",
        contract_version="v1",
        data={
            "proposal": {
                "proposal_id": "pp_1",
                "portfolio_id": "PF_1001",
                "current_state": "RISK_REVIEW",
            },
            "current_version": {
                "proposal_version_id": "ppv_1",
                "proposal_id": "pp_1",
                "version_no": 1,
            },
        },
    )
    version_payload = ProposalVersionEnvelopeResponse(
        correlation_id="corr_4",
        contract_version="v1",
        data={"proposal_version_id": "ppv_1", "proposal_id": "pp_1", "version_no": 1},
    )
    workflow_payload = ProposalWorkflowEventsEnvelopeResponse(
        correlation_id="corr_5",
        contract_version="v1",
        data={"proposal_id": "pp_1", "current_state": "DRAFT", "events": []},
    )
    approvals_payload = ProposalApprovalsEnvelopeResponse(
        correlation_id="corr_6",
        contract_version="v1",
        data={"proposal_id": "pp_1", "current_state": "RISK_REVIEW", "approvals": []},
    )
    lineage_payload = ProposalLineageEnvelopeResponse(
        correlation_id="corr_7",
        contract_version="v1",
        data={"proposal_id": "pp_1", "versions": [{"version_no": 1}]},
    )

    assert list_payload.data.items[0].proposal_id == "pp_1"
    assert detail_payload.data.proposal.current_state == "RISK_REVIEW"
    assert version_payload.data.version_no == 1
    assert workflow_payload.data.proposal_id == "pp_1"
    assert approvals_payload.data.current_state == "RISK_REVIEW"
    assert lineage_payload.data.versions[0].version_no == 1


def test_proposal_write_envelope_contract_shape() -> None:
    payload = ProposalEnvelopeResponse(
        correlation_id="corr_8",
        contract_version="v1",
        data={"proposal": {"proposal_id": "pp_1", "current_state": "DRAFT"}},
    )
    assert payload.data["proposal"]["proposal_id"] == "pp_1"

    create_payload = ProposalCreateEnvelopeResponse(
        correlation_id="corr_9",
        contract_version="v1",
        data={
            "proposal": {"proposal_id": "pp_1", "current_state": "DRAFT"},
            "version": {"proposal_version_id": "ppv_1", "proposal_id": "pp_1", "version_no": 1},
            "latest_workflow_event": {
                "event_id": "pwe_1",
                "event_type": "CREATED",
                "to_state": "DRAFT",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:00:00+00:00",
            },
        },
    )
    transition_payload = ProposalStateTransitionEnvelopeResponse(
        correlation_id="corr_10",
        contract_version="v1",
        data={
            "proposal_id": "pp_1",
            "current_state": "RISK_REVIEW",
            "latest_workflow_event": {
                "event_id": "pwe_2",
                "event_type": "SUBMITTED_FOR_RISK_REVIEW",
                "from_state": "DRAFT",
                "to_state": "RISK_REVIEW",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:07:00+00:00",
            },
        },
    )
    assert create_payload.data.version.version_no == 1
    assert transition_payload.data.latest_workflow_event.event_type == "SUBMITTED_FOR_RISK_REVIEW"


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

    list_response_ref = list_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    detail_response_ref = detail_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    version_response_ref = version_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    events_response_ref = events_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    approvals_response_ref = approvals_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    lineage_response_ref = lineage_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"]

    assert list_response_ref.endswith("/ProposalListEnvelopeResponse")
    assert detail_response_ref.endswith("/ProposalDetailEnvelopeResponse")
    assert version_response_ref.endswith("/ProposalVersionEnvelopeResponse")
    assert events_response_ref.endswith("/ProposalWorkflowEventsEnvelopeResponse")
    assert approvals_response_ref.endswith("/ProposalApprovalsEnvelopeResponse")
    assert lineage_response_ref.endswith("/ProposalLineageEnvelopeResponse")


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

    assert create_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalCreateEnvelopeResponse")
    assert create_version_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalCreateEnvelopeResponse")
    assert submit_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalStateTransitionEnvelopeResponse")
    assert approve_risk_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalStateTransitionEnvelopeResponse")
    assert approve_compliance_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"].endswith("/ProposalStateTransitionEnvelopeResponse")
    assert consent_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalStateTransitionEnvelopeResponse")

    simulate_request_schema = spec["components"]["schemas"]["ProposalSimulateRequest"]
    create_request_schema = spec["components"]["schemas"]["ProposalCreateRequest"]
    version_request_schema = spec["components"]["schemas"]["ProposalVersionCreateRequest"]
    submit_request_schema = spec["components"]["schemas"]["ProposalSubmitRequest"]
    approval_request_schema = spec["components"]["schemas"]["ProposalApprovalActionRequest"]
    simulate_response_schema = spec["components"]["schemas"]["ProposalSimulateResponse"]
    simulate_data_schema = spec["components"]["schemas"]["ProposalSimulationData"]
    list_envelope_schema = spec["components"]["schemas"]["ProposalListEnvelopeResponse"]
    detail_envelope_schema = spec["components"]["schemas"]["ProposalDetailEnvelopeResponse"]
    version_envelope_schema = spec["components"]["schemas"]["ProposalVersionEnvelopeResponse"]
    workflow_envelope_schema = spec["components"]["schemas"][
        "ProposalWorkflowEventsEnvelopeResponse"
    ]
    approvals_envelope_schema = spec["components"]["schemas"]["ProposalApprovalsEnvelopeResponse"]
    lineage_envelope_schema = spec["components"]["schemas"]["ProposalLineageEnvelopeResponse"]
    create_envelope_schema = spec["components"]["schemas"]["ProposalCreateEnvelopeResponse"]
    transition_envelope_schema = spec["components"]["schemas"][
        "ProposalStateTransitionEnvelopeResponse"
    ]
    create_data_schema = spec["components"]["schemas"]["ProposalCreateData"]
    transition_data_schema = spec["components"]["schemas"]["ProposalStateTransitionData"]
    summary_schema = spec["components"]["schemas"]["ProposalSummaryData"]
    version_schema = spec["components"]["schemas"]["ProposalVersionData"]
    workflow_event_schema = spec["components"]["schemas"]["ProposalWorkflowEventData"]
    approval_record_schema = spec["components"]["schemas"]["ProposalApprovalRecordData"]
    lineage_item_schema = spec["components"]["schemas"]["ProposalVersionLineageItemData"]

    assert simulate_request_schema["properties"]["body"]["description"]
    assert simulate_request_schema["properties"]["body"]["examples"][0]["portfolio_id"] == "PF_1001"
    assert create_request_schema["properties"]["body"]["description"]
    assert create_request_schema["properties"]["body"]["examples"][0]["proposal_name"] == (
        "Income tilt rebalance"
    )
    assert version_request_schema["properties"]["body"]["description"]
    assert (
        version_request_schema["properties"]["body"]["examples"][0]["proposed_trades"][0]["action"]
        == "SELL"
    )

    assert submit_request_schema["properties"]["actor_id"]["description"]
    assert submit_request_schema["properties"]["actor_id"]["examples"] == ["advisor_1"]
    assert submit_request_schema["properties"]["expected_state"]["description"]
    assert submit_request_schema["properties"]["expected_state"]["default"] == "DRAFT"
    assert submit_request_schema["properties"]["review_type"]["description"]
    assert submit_request_schema["properties"]["review_type"]["default"] == "RISK"
    assert submit_request_schema["properties"]["related_version_no"]["description"]
    assert submit_request_schema["properties"]["reason"]["description"]
    assert submit_request_schema["properties"]["reason"]["examples"][0]["ticket_id"] == "REQ-102"

    assert approval_request_schema["properties"]["actor_id"]["description"]
    assert approval_request_schema["properties"]["actor_id"]["examples"] == ["risk_1"]
    assert approval_request_schema["properties"]["expected_state"]["description"]
    assert approval_request_schema["properties"]["expected_state"]["examples"] == ["RISK_REVIEW"]
    assert approval_request_schema["properties"]["related_version_no"]["description"]
    assert approval_request_schema["properties"]["details"]["description"]
    assert approval_request_schema["properties"]["details"]["examples"][0]["decision"] == (
        "APPROVED"
    )

    assert simulate_response_schema["properties"]["correlation_id"]["description"]
    assert simulate_response_schema["properties"]["correlation_id"]["examples"] == [
        "corr-proposals-1"
    ]
    assert simulate_response_schema["properties"]["contract_version"]["description"]
    assert simulate_response_schema["properties"]["contract_version"]["default"] == "v1"
    assert simulate_response_schema["properties"]["data"]["description"]
    assert simulate_response_schema["properties"]["data"]["$ref"].endswith(
        "/ProposalSimulationData"
    )
    assert simulate_data_schema["properties"]["proposal_run_id"]["examples"] == ["pr_1"]
    assert simulate_data_schema["properties"]["correlation_id"]["examples"] == ["corr_engine_1"]
    assert simulate_data_schema["properties"]["status"]["examples"] == ["READY"]
    assert simulate_data_schema["properties"]["before"]["description"]
    assert simulate_data_schema["properties"]["intents"]["description"]
    assert simulate_data_schema["properties"]["after_simulated"]["description"]
    assert simulate_data_schema["properties"]["reconciliation"]["description"]
    assert simulate_data_schema["properties"]["rule_results"]["description"]
    assert simulate_data_schema["properties"]["explanation"]["description"]
    assert simulate_data_schema["properties"]["diagnostics"]["description"]
    assert simulate_data_schema["properties"]["drift_analysis"]["description"]
    assert simulate_data_schema["properties"]["suitability"]["description"]
    assert simulate_data_schema["properties"]["gate_decision"]["description"]
    assert simulate_data_schema["properties"]["lineage"]["description"]

    for schema in (
        list_envelope_schema,
        detail_envelope_schema,
        version_envelope_schema,
        workflow_envelope_schema,
        approvals_envelope_schema,
        lineage_envelope_schema,
        create_envelope_schema,
        transition_envelope_schema,
    ):
        assert schema["properties"]["correlation_id"]["description"]
        assert schema["properties"]["correlation_id"]["examples"]
        assert schema["properties"]["contract_version"]["description"]
        assert schema["properties"]["contract_version"]["default"] == "v1"
        assert schema["properties"]["data"]["description"]

    assert summary_schema["properties"]["proposal_id"]["description"]
    assert summary_schema["properties"]["current_state"]["examples"] == ["DRAFT"]
    assert version_schema["properties"]["proposal_version_id"]["description"]
    assert (
        version_schema["properties"]["proposal_result"]["examples"][0]["proposal_run_id"] == "pr_1"
    )
    assert workflow_event_schema["properties"]["event_type"]["examples"] == [
        "SUBMITTED_FOR_RISK_REVIEW"
    ]
    assert approval_record_schema["properties"]["approval_type"]["examples"] == ["RISK"]
    assert lineage_item_schema["properties"]["artifact_hash"]["description"]
    assert create_data_schema["properties"]["proposal"]["description"]
    assert create_data_schema["properties"]["version"]["description"]
    assert create_data_schema["properties"]["latest_workflow_event"]["description"]
    assert transition_data_schema["properties"]["proposal_id"]["description"]
    assert transition_data_schema["properties"]["latest_workflow_event"]["description"]
    assert transition_data_schema["properties"]["approval"]["description"]
