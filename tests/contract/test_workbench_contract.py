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
    overview_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/overview"]["get"]
    portfolio_360_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/portfolio-360"]["get"]
    analytics_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/analytics"]["get"]
    overview_schema = spec["components"]["schemas"]["WorkbenchOverviewResponse"]
    portfolio_summary_schema = spec["components"]["schemas"]["WorkbenchPortfolioSummary"]
    overview_summary_schema = spec["components"]["schemas"]["WorkbenchOverviewSummary"]
    performance_snapshot_schema = spec["components"]["schemas"]["WorkbenchPerformanceSnapshot"]
    rebalance_snapshot_schema = spec["components"]["schemas"]["WorkbenchRebalanceSnapshot"]
    partial_failure_schema = spec["components"]["schemas"]["WorkbenchPartialFailure"]
    portfolio_360_schema = spec["components"]["schemas"]["WorkbenchPortfolio360Response"]
    position_view_schema = spec["components"]["schemas"]["WorkbenchPositionView"]
    projected_position_schema = spec["components"]["schemas"]["WorkbenchProjectedPositionView"]
    projected_summary_schema = spec["components"]["schemas"]["WorkbenchProjectedSummary"]
    analytics_schema = spec["components"]["schemas"]["WorkbenchAnalyticsResponse"]
    analytics_bucket_schema = spec["components"]["schemas"]["WorkbenchAnalyticsBucket"]
    top_change_schema = spec["components"]["schemas"]["WorkbenchTopChange"]
    create_request_schema = spec["components"]["schemas"]["WorkbenchSandboxSessionCreateRequest"]
    change_input_schema = spec["components"]["schemas"]["WorkbenchSandboxChangeInput"]
    apply_request_schema = spec["components"]["schemas"]["WorkbenchSandboxApplyChangesRequest"]
    policy_feedback_schema = spec["components"]["schemas"]["WorkbenchPolicyFeedback"]
    sandbox_response_schema = spec["components"]["schemas"]["WorkbenchSandboxStateResponse"]

    overview_parameters = {
        parameter["name"]: parameter for parameter in overview_operation["parameters"]
    }
    portfolio_360_parameters = {
        parameter["name"]: parameter for parameter in portfolio_360_operation["parameters"]
    }
    analytics_parameters = {
        parameter["name"]: parameter for parameter in analytics_operation["parameters"]
    }
    create_parameters = {
        parameter["name"]: parameter for parameter in create_operation["parameters"]
    }
    apply_parameters = {parameter["name"]: parameter for parameter in apply_operation["parameters"]}

    assert overview_parameters["portfolio_id"]["schema"]["type"] == "string"
    assert overview_parameters["portfolio_id"]["description"]
    assert overview_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert portfolio_360_parameters["portfolio_id"]["schema"]["type"] == "string"
    assert portfolio_360_parameters["portfolio_id"]["description"]
    assert portfolio_360_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert portfolio_360_parameters["session_id"]["schema"]
    assert portfolio_360_parameters["session_id"]["description"]
    assert analytics_parameters["portfolio_id"]["schema"]["type"] == "string"
    assert analytics_parameters["portfolio_id"]["description"]
    assert analytics_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert analytics_parameters["period"]["description"]
    assert analytics_parameters["period"]["schema"]["default"] == "YTD"
    assert analytics_parameters["period"]["schema"]["examples"] == ["YTD"]
    assert analytics_parameters["group_by"]["description"]
    assert analytics_parameters["group_by"]["schema"]["default"] == "ASSET_CLASS"
    assert analytics_parameters["group_by"]["schema"]["examples"] == ["ASSET_CLASS"]
    assert analytics_parameters["benchmark_code"]["description"]
    assert analytics_parameters["benchmark_code"]["schema"]["default"] == "MODEL_60_40"
    assert analytics_parameters["benchmark_code"]["schema"]["examples"] == ["MODEL_60_40"]
    assert analytics_parameters["session_id"]["schema"]
    assert analytics_parameters["session_id"]["description"]

    assert overview_schema["properties"]["correlation_id"]["description"]
    assert overview_schema["properties"]["contract_version"]["description"]
    assert overview_schema["properties"]["as_of_date"]["description"]
    assert overview_schema["properties"]["portfolio"]["description"]
    assert overview_schema["properties"]["overview"]["description"]
    assert overview_schema["properties"]["performance_snapshot"]["description"]
    assert overview_schema["properties"]["rebalance_snapshot"]["description"]
    assert overview_schema["properties"]["warnings"]["description"]
    assert overview_schema["properties"]["partial_failures"]["description"]
    assert portfolio_summary_schema["properties"]["portfolio_id"]["description"]
    assert portfolio_summary_schema["properties"]["client_id"]["description"]
    assert portfolio_summary_schema["properties"]["base_currency"]["description"]
    assert portfolio_summary_schema["properties"]["booking_center_code"]["description"]
    assert overview_summary_schema["properties"]["market_value_base"]["description"]
    assert overview_summary_schema["properties"]["cash_weight_pct"]["description"]
    assert overview_summary_schema["properties"]["position_count"]["description"]
    assert performance_snapshot_schema["properties"]["period"]["description"]
    assert performance_snapshot_schema["properties"]["return_pct"]["description"]
    assert performance_snapshot_schema["properties"]["benchmark_return_pct"]["description"]
    assert rebalance_snapshot_schema["properties"]["status"]["description"]
    assert rebalance_snapshot_schema["properties"]["last_rebalance_run_id"]["description"]
    assert rebalance_snapshot_schema["properties"]["last_run_at_utc"]["description"]
    assert partial_failure_schema["properties"]["source_service"]["description"]
    assert partial_failure_schema["properties"]["error_code"]["description"]
    assert partial_failure_schema["properties"]["detail"]["description"]
    assert portfolio_360_schema["properties"]["current_positions"]["description"]
    assert portfolio_360_schema["properties"]["projected_positions"]["description"]
    assert portfolio_360_schema["properties"]["projected_summary"]["description"]
    assert portfolio_360_schema["properties"]["active_session_id"]["description"]
    assert position_view_schema["properties"]["security_id"]["description"]
    assert position_view_schema["properties"]["instrument_name"]["description"]
    assert position_view_schema["properties"]["asset_class"]["description"]
    assert position_view_schema["properties"]["quantity"]["description"]
    assert position_view_schema["properties"]["market_value_base"]["description"]
    assert position_view_schema["properties"]["weight_pct"]["description"]
    assert projected_position_schema["properties"]["security_id"]["description"]
    assert projected_position_schema["properties"]["instrument_name"]["description"]
    assert projected_position_schema["properties"]["asset_class"]["description"]
    assert projected_position_schema["properties"]["baseline_quantity"]["description"]
    assert projected_position_schema["properties"]["proposed_quantity"]["description"]
    assert projected_position_schema["properties"]["delta_quantity"]["description"]
    assert projected_summary_schema["properties"]["total_baseline_positions"]["description"]
    assert projected_summary_schema["properties"]["total_proposed_positions"]["description"]
    assert projected_summary_schema["properties"]["net_delta_quantity"]["description"]
    assert analytics_schema["properties"]["portfolio_id"]["description"]
    assert analytics_schema["properties"]["session_id"]["description"]
    assert analytics_schema["properties"]["period"]["description"]
    assert analytics_schema["properties"]["group_by"]["description"]
    assert analytics_schema["properties"]["benchmark_code"]["description"]
    assert analytics_schema["properties"]["portfolio_return_pct"]["description"]
    assert analytics_schema["properties"]["benchmark_return_pct"]["description"]
    assert analytics_schema["properties"]["active_return_pct"]["description"]
    assert analytics_schema["properties"]["allocation_buckets"]["description"]
    assert analytics_schema["properties"]["top_changes"]["description"]
    assert analytics_schema["properties"]["warnings"]["description"]
    assert analytics_schema["properties"]["partial_failures"]["description"]
    assert analytics_bucket_schema["properties"]["bucket_key"]["description"]
    assert analytics_bucket_schema["properties"]["bucket_label"]["description"]
    assert analytics_bucket_schema["properties"]["current_quantity"]["description"]
    assert analytics_bucket_schema["properties"]["proposed_quantity"]["description"]
    assert analytics_bucket_schema["properties"]["delta_quantity"]["description"]
    assert analytics_bucket_schema["properties"]["current_weight_pct"]["description"]
    assert analytics_bucket_schema["properties"]["proposed_weight_pct"]["description"]
    assert top_change_schema["properties"]["security_id"]["description"]
    assert top_change_schema["properties"]["instrument_name"]["description"]
    assert top_change_schema["properties"]["delta_quantity"]["description"]
    assert top_change_schema["properties"]["direction"]["description"]

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
