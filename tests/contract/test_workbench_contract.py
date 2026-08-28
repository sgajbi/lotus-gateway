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
                "price": "101.2500000000",
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
    assert "/api/v1/workbench/{portfolio_id}/risk/summary" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/risk/concentration" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/risk/drawdown" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/risk/rolling" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/risk/attribution" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/performance/summary" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/performance/details" in spec["paths"]
    assert (
        "/api/v1/workbench/{portfolio_id}/performance/evidence/artifacts/"
        "{calculation_id}/{artifact_name}"
    ) in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/sandbox/sessions" in spec["paths"]
    assert "/api/v1/workbench/{portfolio_id}/sandbox/sessions/{session_id}/changes" in spec["paths"]
    create_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/sandbox/sessions"]["post"]
    apply_operation = spec["paths"][
        "/api/v1/workbench/{portfolio_id}/sandbox/sessions/{session_id}/changes"
    ]["post"]
    overview_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/overview"]["get"]
    portfolio_360_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/portfolio-360"]["get"]
    analytics_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/analytics"]["get"]
    risk_summary_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/risk/summary"]["get"]
    risk_concentration_operation = spec["paths"][
        "/api/v1/workbench/{portfolio_id}/risk/concentration"
    ]["get"]
    risk_drawdown_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/risk/drawdown"]["get"]
    risk_rolling_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/risk/rolling"]["get"]
    risk_attribution_operation = spec["paths"]["/api/v1/workbench/{portfolio_id}/risk/attribution"][
        "get"
    ]
    performance_summary_operation = spec["paths"][
        "/api/v1/workbench/{portfolio_id}/performance/summary"
    ]["get"]
    performance_details_operation = spec["paths"][
        "/api/v1/workbench/{portfolio_id}/performance/details"
    ]["get"]
    artifact_operation = spec["paths"][
        "/api/v1/workbench/{portfolio_id}/performance/evidence/artifacts/"
        "{calculation_id}/{artifact_name}"
    ]["get"]
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
    risk_summary_schema = spec["components"]["schemas"]["WorkbenchRiskSummaryResponse"]
    risk_concentration_schema = spec["components"]["schemas"]["WorkbenchRiskConcentrationResponse"]
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
    risk_summary_parameters = {
        parameter["name"]: parameter for parameter in risk_summary_operation["parameters"]
    }
    risk_concentration_parameters = {
        parameter["name"]: parameter for parameter in risk_concentration_operation["parameters"]
    }
    risk_drawdown_parameters = {
        parameter["name"]: parameter for parameter in risk_drawdown_operation["parameters"]
    }
    risk_rolling_parameters = {
        parameter["name"]: parameter for parameter in risk_rolling_operation["parameters"]
    }
    risk_attribution_parameters = {
        parameter["name"]: parameter for parameter in risk_attribution_operation["parameters"]
    }
    performance_summary_parameters = {
        parameter["name"]: parameter for parameter in performance_summary_operation["parameters"]
    }
    performance_details_parameters = {
        parameter["name"]: parameter for parameter in performance_details_operation["parameters"]
    }
    artifact_parameters = {
        parameter["name"]: parameter for parameter in artifact_operation["parameters"]
    }
    create_parameters = {
        parameter["name"]: parameter for parameter in create_operation["parameters"]
    }
    apply_parameters = {parameter["name"]: parameter for parameter in apply_operation["parameters"]}

    assert overview_parameters["portfolio_id"]["schema"]["type"] == "string"
    assert overview_parameters["as_of_date"]["description"]
    assert overview_parameters["as_of_date"]["schema"]["examples"] == ["2026-08-23"]
    assert overview_parameters["include_performance_snapshot"]["schema"]["default"] is True
    assert overview_parameters["include_performance_snapshot"]["description"]
    assert (
        "analytics availability"
        in overview_parameters["include_performance_snapshot"]["description"]
    )
    assert overview_parameters["include_rebalance_snapshot"]["schema"]["default"] is True
    assert overview_parameters["include_rebalance_snapshot"]["description"]
    assert (
        "workflow availability" in overview_parameters["include_rebalance_snapshot"]["description"]
    )
    assert "portfolio-360" in overview_operation["description"]
    assert overview_parameters["portfolio_id"]["description"]
    assert overview_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert portfolio_360_parameters["portfolio_id"]["schema"]["type"] == "string"
    assert "sandbox" in portfolio_360_operation["description"].lower()
    assert portfolio_360_parameters["portfolio_id"]["description"]
    assert portfolio_360_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert portfolio_360_parameters["session_id"]["schema"]
    assert portfolio_360_parameters["session_id"]["description"]
    assert portfolio_360_parameters["as_of_date"]["description"]
    assert portfolio_360_parameters["as_of_date"]["schema"]["examples"] == ["2026-08-23"]
    assert analytics_parameters["portfolio_id"]["schema"]["type"] == "string"
    assert "risk proxy" in analytics_operation["description"].lower()
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
    assert risk_summary_parameters["portfolio_id"]["description"]
    assert risk_summary_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert "first-paint" in risk_summary_operation["description"]
    assert risk_summary_parameters["period"]["description"]
    assert "1Y, 3Y, 5Y" in risk_summary_parameters["period"]["description"]
    assert (
        "normalized before calling lotus-risk" in risk_summary_parameters["period"]["description"]
    )
    assert risk_summary_parameters["period"]["schema"]["default"] == "YTD"
    assert risk_summary_parameters["period"]["schema"]["examples"] == ["YTD"]
    assert risk_summary_parameters["detail_basis"]["description"]
    assert risk_summary_parameters["detail_basis"]["schema"]["default"] == "NET"
    assert risk_summary_parameters["detail_basis"]["schema"]["examples"] == ["NET"]
    assert risk_summary_parameters["benchmark_code"]["description"]
    assert risk_summary_parameters["benchmark_code"]["schema"]["examples"] == [
        "BMK_PB_GLOBAL_BALANCED_60_40"
    ]
    assert risk_summary_parameters["as_of_date"]["description"]
    assert risk_summary_parameters["as_of_date"]["schema"]["examples"] == ["2026-02-24"]
    assert risk_summary_parameters["reporting_currency"]["description"]
    assert risk_summary_parameters["reporting_currency"]["schema"]["examples"] == ["USD"]
    assert risk_concentration_parameters["portfolio_id"]["description"]
    assert risk_concentration_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert "issuer mapping coverage" in risk_concentration_operation["description"]
    assert risk_concentration_parameters["period"]["description"]
    assert "1Y, 3Y, 5Y" in risk_concentration_parameters["period"]["description"]
    assert risk_concentration_parameters["period"]["schema"]["default"] == "YTD"
    assert risk_concentration_parameters["period"]["schema"]["examples"] == ["YTD"]
    assert risk_concentration_parameters["benchmark_code"]["description"]
    assert risk_concentration_parameters["benchmark_code"]["schema"]["examples"] == [
        "BMK_PB_GLOBAL_BALANCED_60_40"
    ]
    assert risk_concentration_parameters["as_of_date"]["description"]
    assert risk_concentration_parameters["as_of_date"]["schema"]["examples"] == ["2026-02-24"]
    assert risk_concentration_parameters["reporting_currency"]["description"]
    assert risk_concentration_parameters["reporting_currency"]["schema"]["examples"] == ["USD"]
    assert risk_drawdown_parameters["portfolio_id"]["description"]
    assert risk_drawdown_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert "include_underwater_series=true" in risk_drawdown_operation["description"]
    assert risk_drawdown_parameters["period"]["description"]
    assert "1Y, 3Y, 5Y" in risk_drawdown_parameters["period"]["description"]
    assert risk_drawdown_parameters["period"]["schema"]["default"] == "YTD"
    assert risk_drawdown_parameters["detail_basis"]["description"]
    assert risk_drawdown_parameters["detail_basis"]["schema"]["default"] == "NET"
    assert risk_drawdown_parameters["benchmark_code"]["description"]
    assert risk_drawdown_parameters["benchmark_code"]["schema"]["examples"] == [
        "BMK_PB_GLOBAL_BALANCED_60_40"
    ]
    assert risk_drawdown_parameters["as_of_date"]["description"]
    assert risk_drawdown_parameters["as_of_date"]["schema"]["examples"] == ["2026-02-24"]
    assert risk_drawdown_parameters["reporting_currency"]["description"]
    assert risk_drawdown_parameters["reporting_currency"]["schema"]["examples"] == ["USD"]
    assert risk_drawdown_parameters["include_underwater_series"]["description"]
    assert risk_drawdown_parameters["include_underwater_series"]["schema"]["default"] is False
    assert risk_drawdown_parameters["include_underwater_series"]["schema"]["examples"] == [True]
    assert risk_rolling_parameters["portfolio_id"]["description"]
    assert risk_rolling_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert "include_time_series=true" in risk_rolling_operation["description"]
    assert "omits rolling sharpe" in risk_rolling_operation["description"].lower()
    assert risk_rolling_parameters["period"]["description"]
    assert "1Y, 3Y, 5Y" in risk_rolling_parameters["period"]["description"]
    assert risk_rolling_parameters["period"]["schema"]["default"] == "YTD"
    assert risk_rolling_parameters["detail_basis"]["description"]
    assert risk_rolling_parameters["detail_basis"]["schema"]["default"] == "NET"
    assert risk_rolling_parameters["benchmark_code"]["description"]
    assert risk_rolling_parameters["benchmark_code"]["schema"]["examples"] == [
        "BMK_PB_GLOBAL_BALANCED_60_40"
    ]
    assert risk_rolling_parameters["as_of_date"]["description"]
    assert risk_rolling_parameters["as_of_date"]["schema"]["examples"] == ["2026-02-24"]
    assert risk_rolling_parameters["reporting_currency"]["description"]
    assert risk_rolling_parameters["reporting_currency"]["schema"]["examples"] == ["USD"]
    assert risk_rolling_parameters["include_time_series"]["description"]
    assert risk_rolling_parameters["include_time_series"]["schema"]["default"] is False
    assert risk_rolling_parameters["include_time_series"]["schema"]["examples"] == [True]
    assert risk_attribution_parameters["portfolio_id"]["description"]
    assert risk_attribution_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert "total-risk or active-risk decomposition" in risk_attribution_operation["description"]
    assert (
        "benchmark-required and grouping-gated combinations"
        in (risk_attribution_operation["description"])
    )
    assert risk_attribution_parameters["period"]["description"]
    assert "1Y, 3Y, 5Y" in risk_attribution_parameters["period"]["description"]
    assert risk_attribution_parameters["period"]["schema"]["default"] == "YTD"
    assert risk_attribution_parameters["detail_basis"]["description"]
    assert risk_attribution_parameters["detail_basis"]["schema"]["default"] == "NET"
    assert risk_attribution_parameters["benchmark_code"]["description"]
    assert risk_attribution_parameters["benchmark_code"]["schema"]["examples"] == [
        "BMK_PB_GLOBAL_BALANCED_60_40"
    ]
    assert risk_attribution_parameters["as_of_date"]["description"]
    assert risk_attribution_parameters["as_of_date"]["schema"]["examples"] == ["2026-02-24"]
    assert risk_attribution_parameters["reporting_currency"]["description"]
    assert risk_attribution_parameters["reporting_currency"]["schema"]["examples"] == ["USD"]
    assert risk_attribution_parameters["attribution_type"]["description"]
    assert risk_attribution_parameters["attribution_type"]["schema"]["default"] == "TOTAL_RISK"
    assert risk_attribution_parameters["attribution_type"]["schema"]["examples"] == ["ACTIVE_RISK"]
    assert risk_attribution_parameters["grouping_dimension"]["description"]
    assert risk_attribution_parameters["grouping_dimension"]["schema"]["default"] == "SECTOR"
    assert risk_attribution_parameters["grouping_dimension"]["schema"]["examples"] == ["SECTOR"]
    assert performance_summary_parameters["portfolio_id"]["description"]
    assert performance_summary_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert "governed monotonic deadline" in performance_summary_operation["description"]
    assert "partial-readiness" in performance_summary_operation["description"]
    assert performance_summary_parameters["period"]["description"]
    assert "2Y" in performance_summary_parameters["period"]["description"]
    assert "10Y" in performance_summary_parameters["period"]["description"]
    assert "SI" in performance_summary_parameters["period"]["description"]
    assert "typed 422" in performance_summary_parameters["period"]["description"]
    assert performance_summary_parameters["period"]["schema"]["default"] == "YTD"
    assert performance_summary_parameters["chart_frequency"]["description"]
    assert performance_summary_parameters["chart_frequency"]["schema"]["default"] == "monthly"
    assert performance_summary_parameters["contribution_dimension"]["description"]
    assert (
        performance_summary_parameters["contribution_dimension"]["schema"]["default"]
        == "asset_class"
    )
    assert performance_summary_parameters["attribution_dimension"]["description"]
    assert (
        performance_summary_parameters["attribution_dimension"]["schema"]["default"]
        == "asset_class"
    )
    assert performance_summary_parameters["detail_basis"]["description"]
    assert performance_summary_parameters["detail_basis"]["schema"]["default"] == "NET"
    assert performance_summary_parameters["benchmark_code"]["description"]
    assert performance_summary_parameters["benchmark_code"]["schema"]["examples"] == [
        "BMK_PB_GLOBAL_BALANCED_60_40"
    ]
    assert performance_summary_parameters["report_start_date"]["description"]
    assert performance_summary_parameters["report_start_date"]["schema"]["examples"] == [
        "2026-01-01"
    ]
    assert performance_summary_parameters["report_end_date"]["description"]
    assert performance_summary_parameters["report_end_date"]["schema"]["examples"] == ["2026-03-27"]
    assert performance_details_parameters["portfolio_id"]["description"]
    assert performance_details_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert performance_details_parameters["period"]["description"]
    assert "2Y" in performance_details_parameters["period"]["description"]
    assert "10Y" in performance_details_parameters["period"]["description"]
    assert "SI" in performance_details_parameters["period"]["description"]
    assert "typed 422" in performance_details_parameters["period"]["description"]
    assert performance_details_parameters["period"]["schema"]["default"] == "YTD"
    assert performance_details_parameters["chart_frequency"]["description"]
    assert performance_details_parameters["chart_frequency"]["schema"]["default"] == "monthly"
    assert performance_details_parameters["contribution_dimension"]["description"]
    assert (
        performance_details_parameters["contribution_dimension"]["schema"]["default"]
        == "asset_class"
    )
    assert performance_details_parameters["attribution_dimension"]["description"]
    assert (
        performance_details_parameters["attribution_dimension"]["schema"]["default"]
        == "asset_class"
    )
    assert performance_details_parameters["detail_basis"]["description"]
    assert performance_details_parameters["detail_basis"]["schema"]["default"] == "NET"
    assert performance_details_parameters["benchmark_code"]["description"]
    assert performance_details_parameters["benchmark_code"]["schema"]["examples"] == [
        "BMK_PB_GLOBAL_BALANCED_60_40"
    ]
    assert performance_details_parameters["report_start_date"]["description"]
    assert performance_details_parameters["report_start_date"]["schema"]["examples"] == [
        "2026-01-01"
    ]
    assert performance_details_parameters["report_end_date"]["description"]
    assert performance_details_parameters["report_end_date"]["schema"]["examples"] == ["2026-03-27"]
    assert artifact_parameters["portfolio_id"]["description"]
    assert artifact_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert "evidence_view.calculations[].artifacts[]" in artifact_operation["description"]
    assert "preserves the upstream content type" in artifact_operation["description"]
    assert artifact_parameters["calculation_id"]["description"]
    assert artifact_parameters["calculation_id"]["schema"]["examples"] == ["calc-workspace-summary"]
    assert artifact_parameters["artifact_name"]["description"]
    assert artifact_parameters["artifact_name"]["schema"]["examples"] == ["request.json"]

    assert overview_schema["properties"]["correlation_id"]["description"]
    assert overview_schema["example"]["portfolio"]["portfolio_id"] == "PF_1001"
    assert overview_schema["example"]["rebalance_snapshot"]["status"] == "PENDING_REVIEW"
    assert overview_schema["properties"]["contract_version"]["description"]
    assert overview_schema["properties"]["as_of_date"]["description"]
    assert overview_schema["properties"]["requested_as_of_date"]["description"]
    assert overview_schema["properties"]["effective_as_of_date"]["description"]
    assert overview_schema["properties"]["as_of_state"]["description"]
    assert overview_schema["properties"]["portfolio"]["description"]
    assert overview_schema["properties"]["overview"]["description"]
    assert overview_schema["properties"]["performance_snapshot"]["description"]
    assert overview_schema["properties"]["rebalance_snapshot"]["description"]
    assert (
        overview_schema["example"]["rebalance_snapshot"]["supportability"]["feature_key"]
        == "manage.observability.action_register_supportability"
    )
    assert (
        overview_schema["example"]["rebalance_snapshot"]["recent_runs"][0]["workflow_state"]
        == "PM_REVIEW_REQUIRED"
    )
    assert overview_schema["properties"]["warnings"]["description"]
    assert overview_schema["properties"]["partial_failures"]["description"]
    assert portfolio_summary_schema["properties"]["portfolio_id"]["description"]
    assert portfolio_360_schema["properties"]["as_of_date"]["description"]
    assert portfolio_360_schema["properties"]["requested_as_of_date"]["description"]
    assert portfolio_360_schema["properties"]["effective_as_of_date"]["description"]
    assert portfolio_360_schema["properties"]["as_of_state"]["description"]
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
    assert rebalance_snapshot_schema["properties"]["supportability"]["description"]
    assert rebalance_snapshot_schema["properties"]["recent_runs"]["description"]
    rebalance_run_schema = spec["components"]["schemas"]["WorkbenchRebalanceRunSummary"]
    assert rebalance_run_schema["properties"]["rebalance_run_id"]["description"]
    assert rebalance_run_schema["properties"]["status"]["description"]
    assert rebalance_run_schema["properties"]["created_at_utc"]["description"]
    assert rebalance_run_schema["properties"]["error_code"]["description"]
    assert rebalance_run_schema["properties"]["workflow_state"]["description"]
    assert partial_failure_schema["properties"]["source_service"]["description"]
    assert partial_failure_schema["properties"]["error_code"]["description"]
    assert partial_failure_schema["properties"]["detail"]["description"]
    assert portfolio_360_schema["properties"]["current_positions"]["description"]
    assert portfolio_360_schema["example"]["current_positions"][0]["instrument_name"] == "Equity 1"
    assert portfolio_360_schema["example"]["active_session_id"] == "sess_1"
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
    assert analytics_schema["example"]["benchmark_code"] == "MODEL_60_40"
    assert analytics_schema["example"]["warnings"] == ["RISK_BFF_PENDING"]
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
    assert risk_summary_schema["properties"]["correlation_id"]["description"]
    assert risk_summary_schema["properties"]["correlation_id"]["examples"] == [
        "corr-risk-summary-1"
    ]
    assert risk_summary_schema["properties"]["contract_version"]["description"]
    assert risk_summary_schema["properties"]["contract_version"]["default"] == "risk-workspace.v1"
    assert risk_summary_schema["properties"]["portfolio_id"]["description"]
    assert risk_summary_schema["properties"]["period"]["description"]
    assert risk_summary_schema["properties"]["as_of_date"]["description"]
    assert risk_summary_schema["properties"]["benchmark_code"]["description"]
    assert risk_summary_schema["properties"]["source_service"]["description"]
    assert risk_summary_schema["properties"]["state"]["description"]
    assert risk_summary_schema["properties"]["supportability"]["description"]
    assert risk_summary_schema["properties"]["warnings"]["description"]
    assert risk_summary_schema["properties"]["partial_failures"]["description"]
    assert risk_summary_schema["properties"]["metadata"]["description"]
    assert risk_summary_schema["properties"]["mandate_comparison"]["description"]
    assert (
        risk_summary_schema["example"]["payload"]["periods"][0]["metrics"][0]["key"] == "VOLATILITY"
    )
    assert (
        risk_summary_schema["example"]["payload"]["periods"][0]["metrics"][1]["state"] == "partial"
    )
    assert risk_summary_schema["example"]["supportability"][1]["key"] == "risk_free_series"
    assert risk_summary_schema["example"]["warnings"] == ["RISK_SUMMARY_PARTIAL"]
    assert risk_summary_schema["example"]["mandate_comparison"]["risk_profile"] == "BALANCED"
    assert (
        risk_summary_schema["example"]["mandate_comparison"]["constraints"][0]["state"] == "within"
    )
    assert risk_concentration_schema["properties"]["mandate_comparison"]["description"]
    assert (
        risk_concentration_schema["example"]["mandate_comparison"]["constraints"][1]["state"]
        == "breach"
    )
    assert (
        risk_summary_schema["example"]["partial_failures"][0]["error_code"]
        == "RISK_FREE_UNAVAILABLE"
    )
    metric_schema = spec["components"]["schemas"]["WorkbenchRiskMetric"]
    period_result_schema = spec["components"]["schemas"]["WorkbenchRiskPeriodResult"]
    supportability_item_schema = spec["components"]["schemas"]["WorkbenchRiskSupportabilityItem"]
    metadata_schema = spec["components"]["schemas"]["WorkbenchRiskMetadata"]
    summary_payload_schema = spec["components"]["schemas"]["WorkbenchRiskSummaryPayload"]
    mandate_comparison_schema = spec["components"]["schemas"]["WorkbenchMandateComparison"]
    mandate_constraint_schema = spec["components"]["schemas"][
        "WorkbenchMandateConstraintComparison"
    ]
    mandate_review_policy_schema = spec["components"]["schemas"]["WorkbenchMandateReviewPolicy"]
    assert mandate_comparison_schema["properties"]["comparison_as_of_date"]["description"]
    assert mandate_comparison_schema["properties"]["date_alignment_state"]["description"]
    assert mandate_comparison_schema["properties"]["source_lineage"]["description"]
    assert mandate_constraint_schema["properties"]["headroom"]["description"]
    assert mandate_constraint_schema["properties"]["source_state"]["description"]
    review_frequency_schema = mandate_review_policy_schema["properties"]["review_frequency"]
    assert review_frequency_schema["description"]
    assert {variant.get("type") for variant in review_frequency_schema["anyOf"]} == {
        "string",
        "null",
    }
    assert "review_frequency" not in mandate_review_policy_schema.get("required", [])
    assert metric_schema["properties"]["key"]["description"]
    assert metric_schema["properties"]["value"]["examples"] == [0.12]
    assert metric_schema["properties"]["details"]["description"]
    assert period_result_schema["properties"]["portfolio_observation_count"]["description"]
    assert (
        period_result_schema["properties"]["benchmark_context"]["examples"][0]["reason"]
        == "APPLIED"
    )
    assert supportability_item_schema["properties"]["state"]["description"]
    assert supportability_item_schema["properties"]["source_service"]["examples"] == ["lotus-risk"]
    assert metadata_schema["properties"]["generated_at"]["description"]
    assert summary_payload_schema["properties"]["periods"]["description"]
    concentration_schema = spec["components"]["schemas"]["WorkbenchRiskConcentrationResponse"]
    concentration_payload_schema = spec["components"]["schemas"][
        "WorkbenchRiskConcentrationPayload"
    ]
    issuer_concentration_schema = spec["components"]["schemas"]["WorkbenchIssuerConcentration"]
    execution_context_schema = spec["components"]["schemas"][
        "WorkbenchRiskConcentrationExecutionContext"
    ]
    valuation_context_schema = spec["components"]["schemas"][
        "WorkbenchRiskConcentrationValuationContext"
    ]
    single_position_schema = spec["components"]["schemas"]["WorkbenchSinglePositionConcentration"]
    top_position_schema = spec["components"]["schemas"]["WorkbenchTopPositionDriver"]
    top_issuer_schema = spec["components"]["schemas"]["WorkbenchTopIssuerDriver"]
    assert (
        concentration_schema["example"]["payload"]["issuer_concentration"]["coverage_status"]
        == "complete"
    )
    assert (
        concentration_schema["example"]["payload"]["execution_context"]["issuer_grouping_level"]
        == "ultimate_parent"
    )
    assert concentration_schema["example"]["supportability"][1]["key"] == "issuer_enrichment"
    assert (
        concentration_schema["example"]["partial_failures"][0]["error_code"]
        == "ISSUER_ENRICHMENT_PARTIAL"
    )
    assert concentration_payload_schema["example"]["portfolio_concentration"]["hhi_delta"] == 25.0
    assert issuer_concentration_schema["properties"]["coverage_ratio_current"]["description"]
    assert issuer_concentration_schema["properties"]["top_issuer_current"]["description"]
    assert execution_context_schema["properties"]["enrichment_policy"]["description"]
    assert valuation_context_schema["properties"]["weight_basis"]["examples"] == [
        "total_market_value_base"
    ]
    assert single_position_schema["properties"]["top_n"]["description"]
    assert top_position_schema["properties"]["security_name"]["examples"] == [
        "PIMCO GIS Income Fund"
    ]
    assert top_issuer_schema["properties"]["issuer_name"]["examples"] == [
        "Pacific Investment Management Company LLC"
    ]
    drawdown_schema = spec["components"]["schemas"]["WorkbenchRiskDrawdownResponse"]
    drawdown_payload_schema = spec["components"]["schemas"]["WorkbenchRiskDrawdownPayload"]
    drawdown_period_schema = spec["components"]["schemas"]["WorkbenchRiskDrawdownPeriodResult"]
    drawdown_summary_schema = spec["components"]["schemas"]["WorkbenchRiskDrawdownSummary"]
    drawdown_episode_schema = spec["components"]["schemas"]["WorkbenchRiskDrawdownEpisode"]
    relative_drawdown_schema = spec["components"]["schemas"]["WorkbenchRiskRelativeDrawdownSummary"]
    relative_context_schema = spec["components"]["schemas"]["WorkbenchRiskRelativeDrawdownContext"]
    underwater_point_schema = spec["components"]["schemas"]["WorkbenchRiskUnderwaterPoint"]
    analysis_context_schema = spec["components"]["schemas"]["WorkbenchRiskDrawdownAnalysisContext"]
    assert (
        drawdown_schema["example"]["payload"]["periods"][0]["summary"]["max_drawdown"] == -0.124533
    )
    assert (
        drawdown_schema["example"]["payload"]["periods"][0]["relative_to_benchmark_context"][
            "reason"
        ]
        == "APPLIED"
    )
    assert drawdown_schema["example"]["supportability"][2]["key"] == "underwater_series"
    assert (
        drawdown_schema["example"]["partial_failures"][0]["error_code"]
        == "BENCHMARK_RELATIVE_DRAWDOWN_UNAVAILABLE"
    )
    assert drawdown_payload_schema["properties"]["periods"]["description"]
    assert drawdown_period_schema["properties"]["underwater_series"]["description"]
    assert drawdown_summary_schema["properties"]["ulcer_index"]["description"]
    assert drawdown_summary_schema["properties"]["conditional_drawdown_at_risk_95"]["examples"] == [
        -0.117884
    ]
    assert drawdown_episode_schema["properties"]["depth"]["examples"] == [-0.124533]
    assert relative_drawdown_schema["properties"]["time_under_water_days"]["description"]
    assert relative_context_schema["properties"]["aligned_observation_count"]["examples"] == [36]
    assert underwater_point_schema["properties"]["drawdown"]["examples"] == [-0.0521]
    assert analysis_context_schema["properties"]["include_underwater_series"]["description"]
    rolling_schema = spec["components"]["schemas"]["WorkbenchRiskRollingResponse"]
    rolling_payload_schema = spec["components"]["schemas"]["WorkbenchRiskRollingPayload"]
    rolling_period_schema = spec["components"]["schemas"]["WorkbenchRiskRollingPeriodResult"]
    rolling_window_schema = spec["components"]["schemas"]["WorkbenchRiskRollingWindowResult"]
    rolling_summary_schema = spec["components"]["schemas"]["WorkbenchRiskRollingMetricSummary"]
    rolling_series_schema = spec["components"]["schemas"]["WorkbenchRiskRollingMetricSeriesPoint"]
    rolling_series_context_schema = spec["components"]["schemas"][
        "WorkbenchRiskRollingMetricSeriesContext"
    ]
    rolling_dependency_schema = spec["components"]["schemas"][
        "WorkbenchRiskRollingDependencyContext"
    ]
    rolling_request_schema = spec["components"]["schemas"]["WorkbenchRiskRollingRequestContext"]
    rolling_request_dependency_schema = spec["components"]["schemas"][
        "WorkbenchRiskRollingRequestDependencyContext"
    ]
    assert rolling_schema["example"]["payload"]["periods"][0]["series_count"] == 66
    assert (
        rolling_schema["example"]["payload"]["periods"][0]["risk_free_context"]["reason"]
        == "Risk-free series could not be aligned for rolling Sharpe."
    )
    assert rolling_schema["example"]["supportability"][2]["key"] == "risk_free_series"
    assert rolling_schema["example"]["warnings"] == [
        "RISK_ROLLING_QUALITY_FLAGS",
        "RISK_ROLLING_SHARPE_PARTIAL",
    ]
    assert (
        rolling_schema["example"]["partial_failures"][0]["error_code"]
        == "ROLLING_SHARPE_UNAVAILABLE"
    )
    assert rolling_payload_schema["properties"]["request_context"]["description"]
    assert rolling_period_schema["properties"]["window_lengths_requested"]["description"]
    assert rolling_period_schema["properties"]["aligned_risk_free_series_count"]["examples"] == [0]
    assert rolling_window_schema["properties"]["metric_series_context"]["description"]
    assert rolling_summary_schema["properties"]["coverage_ratio"]["description"]
    assert rolling_summary_schema["properties"]["latest"]["examples"] == [0.1374]
    assert rolling_series_schema["properties"]["metric_values"]["description"]
    assert rolling_series_context_schema["properties"]["reason"]["description"]
    assert rolling_dependency_schema["properties"]["aligned"]["description"]
    assert rolling_request_schema["properties"]["include_time_series"]["description"]
    assert rolling_request_dependency_schema["properties"]["requested_metrics"]["examples"] == [
        ["ROLLING_SHARPE"]
    ]
    attribution_schema = spec["components"]["schemas"]["WorkbenchRiskAttributionResponse"]
    attribution_payload_schema = spec["components"]["schemas"]["WorkbenchRiskAttributionPayload"]
    attribution_controls_schema = spec["components"]["schemas"]["WorkbenchRiskAttributionControls"]
    attribution_period_schema = spec["components"]["schemas"][
        "WorkbenchRiskAttributionPeriodResult"
    ]
    attribution_set_schema = spec["components"]["schemas"]["WorkbenchRiskAttributionSet"]
    attribution_contributor_schema = spec["components"]["schemas"][
        "WorkbenchRiskAttributionContributor"
    ]
    attribution_type_schema = spec["components"]["schemas"]["WorkbenchRiskAttributionTypeOption"]
    attribution_grouping_schema = spec["components"]["schemas"][
        "WorkbenchRiskAttributionGroupingOption"
    ]
    attribution_methodology_schema = spec["components"]["schemas"][
        "WorkbenchRiskAttributionMethodologyContext"
    ]
    assert attribution_schema["example"]["payload"]["controls"]["selected_attribution_type"] == (
        "ACTIVE_RISK"
    )
    assert (
        attribution_schema["example"]["payload"]["controls"]["grouping_dimensions"][3]["state"]
        == "blocked"
    )
    assert attribution_schema["example"]["supportability"][3]["key"] == (
        "benchmark_exposure_context"
    )
    assert attribution_schema["example"]["warnings"] == ["RISK_ATTRIBUTION_PARTIAL"]
    assert (
        attribution_schema["example"]["partial_failures"][0]["error_code"]
        == "RISK_ATTRIBUTION_PERIOD_ERROR"
    )
    assert attribution_payload_schema["properties"]["controls"]["description"]
    assert attribution_controls_schema["properties"]["selected_grouping_dimension"]["description"]
    assert attribution_period_schema["properties"]["attribution_sets"]["description"]
    assert attribution_set_schema["properties"]["quality_flags"]["description"]
    assert attribution_contributor_schema["properties"]["percent_contribution"]["description"]
    assert attribution_type_schema["properties"]["state"]["description"]
    assert attribution_grouping_schema["properties"]["supported_attribution_types"]["examples"][
        0
    ] == ["TOTAL_RISK", "ACTIVE_RISK"]
    assert attribution_methodology_schema["properties"][
        "stateful_active_risk_gated_grouping_dimensions"
    ]["examples"][0] == ["ISSUER"]

    assert create_parameters["portfolio_id"]["schema"]["type"] == "string"
    assert "projected baseline state" in create_operation["description"].lower()
    assert create_parameters["portfolio_id"]["description"]
    assert create_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert apply_parameters["portfolio_id"]["schema"]["type"] == "string"
    assert "incremental" in apply_operation["description"].lower()
    assert apply_parameters["portfolio_id"]["description"]
    assert apply_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert apply_parameters["session_id"]["schema"]["type"] == "string"
    assert apply_parameters["session_id"]["description"]
    assert apply_parameters["session_id"]["schema"]["examples"] == ["sess_1"]
    assert create_operation["requestBody"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/WorkbenchSandboxSessionCreateRequest"
    )
    assert apply_operation["requestBody"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/WorkbenchSandboxApplyChangesRequest"
    )
    assert create_request_schema["properties"]["created_by"]["description"]
    assert create_request_schema["example"]["ttl_hours"] == 24
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
    assert apply_request_schema["example"]["changes"][0]["security_id"] == "EQ_1"
    assert apply_request_schema["properties"]["evaluate_policy"]["description"]
    assert policy_feedback_schema["properties"]["status"]["description"]
    assert policy_feedback_schema["example"]["raw"]["gate_decision"]["status"] == "PASS"
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
    assert sandbox_response_schema["example"]["projected_positions"][0]["security_id"] == "EQ_1"
    assert sandbox_response_schema["example"]["policy_feedback"]["status"] == "PASS"
