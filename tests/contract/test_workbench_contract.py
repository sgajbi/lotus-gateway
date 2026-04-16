from fastapi.testclient import TestClient

from app.contracts.workbench import (
    WorkbenchOverviewResponse,
    WorkbenchSandboxApplyChangesRequest,
    WorkbenchSandboxStateResponse,
)
from app.main import app


def test_workbench_response_model_contract_shape() -> None:
    payload = WorkbenchOverviewResponse(
        correlation_id="corr_1",
        contract_version="v1",
        as_of_date="2026-02-23",
        portfolio={
            "portfolio_id": "PF_1001",
            "client_id": "CIF_1001",
            "base_currency": "USD",
            "booking_center_code": "SG",
        },
        overview={
            "market_value_base": 1000.0,
            "cash_weight_pct": 0.2,
            "position_count": 5,
        },
    )
    assert payload.portfolio.portfolio_id == "PF_1001"
    assert payload.overview.position_count == 5


def test_workbench_sandbox_contract_shape() -> None:
    request = WorkbenchSandboxApplyChangesRequest(
        changes=[
            {
                "security_id": "EQ_1",
                "transaction_type": "BUY",
                "quantity": 2,
                "price": 101.25,
                "currency": "USD",
                "effective_date": "2026-02-24",
            }
        ],
        evaluate_policy=True,
    )
    response = WorkbenchSandboxStateResponse(
        correlation_id="corr-workbench-sandbox-1",
        contract_version="v1",
        portfolio_id="PF_1001",
        session_id="sess_1",
        session_version=2,
        projected_positions=[
            {
                "security_id": "EQ_1",
                "instrument_name": "Equity 1",
                "asset_class": "Equity",
                "baseline_quantity": 10,
                "proposed_quantity": 12,
                "delta_quantity": 2,
            }
        ],
        projected_summary={
            "total_baseline_positions": 1,
            "total_proposed_positions": 1,
            "net_delta_quantity": 2.0,
        },
        policy_feedback={"status": "PASS", "detail": "Simulation passed portfolio policy checks."},
    )

    assert request.changes[0].security_id == "EQ_1"
    assert request.evaluate_policy is True
    assert response.session_id == "sess_1"
    assert response.policy_feedback is not None
    assert response.policy_feedback.status == "PASS"


def test_workbench_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    assert "/api/v1/workbench/{portfolio_id}/overview" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/portfolio-360" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/analytics" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/sandbox/sessions" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/sandbox/sessions/{session_id}/changes" in spec["paths"]
    create_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/sandbox/sessions"]["post"]
    apply_operation = spec["paths"][
        "/api/v1/workbench/{portfolio_id}/sandbox/sessions/{session_id}/changes"
    ]["post"]
    create_request_schema = spec["components"]["schemas"]["WorkbenchSandboxSessionCreateRequest"]
    change_input_schema = spec["components"]["schemas"]["WorkbenchSandboxChangeInput"]
    apply_request_schema = spec["components"]["schemas"]["WorkbenchSandboxApplyChangesRequest"]
    policy_feedback_schema = spec["components"]["schemas"]["WorkbenchPolicyFeedback"]
    sandbox_response_schema = spec["components"]["schemas"]["WorkbenchSandboxStateResponse"]

    create_parameters = {
        parameter["name"]: parameter for parameter in create_operation["parameters"]
    }
    apply_parameters = {parameter["name"]: parameter for parameter in apply_operation["parameters"]}
    assert create_parameters["portfolio_id"]["schema"]["type"] == "string"
    assert apply_parameters["portfolio_id"]["schema"]["type"] == "string"
    assert apply_parameters["session_id"]["schema"]["type"] == "string"
    assert create_operation["requestBody"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/WorkbenchSandboxSessionCreateRequest"
    )
    assert apply_operation["requestBody"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/WorkbenchSandboxApplyChangesRequest"
    )
    assert create_request_schema["properties"]["created_by"]["description"]
    assert create_request_schema["properties"]["ttl_hours"]["description"]
    assert change_input_schema["properties"]["security_id"]["description"]
    assert change_input_schema["properties"]["transaction_type"]["description"]
    assert change_input_schema["properties"]["quantity"]["description"]
    assert change_input_schema["properties"]["price"]["description"]
    assert change_input_schema["properties"]["amount"]["description"]
    assert change_input_schema["properties"]["currency"]["description"]
    assert change_input_schema["properties"]["effective_date"]["description"]
    assert change_input_schema["properties"]["metadata"]["description"]
    assert apply_request_schema["properties"]["changes"]["description"]
    assert apply_request_schema["properties"]["evaluate_policy"]["description"]
    assert policy_feedback_schema["properties"]["status"]["description"]
    assert policy_feedback_schema["properties"]["detail"]["description"]
    assert policy_feedback_schema["properties"]["raw"]["description"]
    assert sandbox_response_schema["properties"]["correlation_id"]["description"]
    assert sandbox_response_schema["properties"]["contract_version"]["description"]
    assert sandbox_response_schema["properties"]["portfolio_id"]["description"]
    assert sandbox_response_schema["properties"]["session_id"]["description"]
    assert sandbox_response_schema["properties"]["session_version"]["description"]
    assert sandbox_response_schema["properties"]["projected_positions"]["description"]
    assert sandbox_response_schema["properties"]["projected_summary"]["description"]
    assert sandbox_response_schema["properties"]["policy_feedback"]["description"]
    assert sandbox_response_schema["properties"]["warnings"]["description"]
    assert sandbox_response_schema["properties"]["partial_failures"]["description"]
