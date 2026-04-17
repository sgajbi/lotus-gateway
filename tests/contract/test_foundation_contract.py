from fastapi.testclient import TestClient

from app.contracts.foundation import FoundationWorkspaceResponse
from app.main import app


def test_foundation_response_model_contract_shape() -> None:
    payload = FoundationWorkspaceResponse(
        correlation_id="corr_1",
        contract_version="v1",
        as_of_date="2026-03-26",
        portfolio={
            "portfolio_id": "PF_1001",
            "display_name": "Alpha Growth",
            "client_id": "CIF_1001",
            "base_currency": "USD",
            "booking_center_code": "SG",
        },
        summary={
            "market_value_base": 1000.0,
            "total_cash_base": 100.0,
            "cash_weight_pct": 10.0,
            "position_count": 3,
        },
        allocations=[
            {
                "asset_class": "Equity",
                "position_count": 2,
                "market_value_base": 900.0,
                "weight_pct": 90.0,
            }
        ],
        top_positions=[
            {
                "security_id": "EQ_1",
                "display_name": "Global Equity Fund",
                "asset_class": "Equity",
                "market_value_base": 600.0,
                "weight_pct": 60.0,
            }
        ],
        performance={"period": "YTD", "return_pct": 4.2},
        rebalance={"status": "READY"},
        readiness={"has_positions": True, "reporting": {"status": "READY", "row_count": 2}},
        workflow_cues=[
            {"key": "performance", "label": "Open Performance", "href": "/app/performance"}
        ],
        evidence={
            "status": "ready",
            "summary": "Foundation workspace inputs are ready for advisor use.",
            "warning_count": 0,
            "partial_failure_count": 0,
            "affected_sources": [],
        },
    )
    assert payload.portfolio.portfolio_id == "PF_1001"
    assert payload.summary.position_count == 3
    assert payload.top_positions[0].security_id == "EQ_1"
    assert payload.readiness.reporting.status == "READY"
    assert payload.evidence.status == "ready"


def test_foundation_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    assert "/api/v1/foundation/portfolios" in spec["paths"]
    assert "/api/v1/foundation/portfolios/{portfolio_id}/workspace" in spec["paths"]
    catalog_operation = spec["paths"]["/api/v1/foundation/portfolios"]["get"]
    workspace_operation = spec["paths"]["/api/v1/foundation/portfolios/{portfolio_id}/workspace"][
        "get"
    ]
    assert "selector-ready catalog" in catalog_operation["description"].lower()
    assert "client and booking-center codes" in catalog_operation["description"].lower()
    assert "top positions" in workspace_operation["description"].lower()
    parameters = {
        parameter["name"]: parameter
        for parameter in workspace_operation["parameters"]
        if parameter["in"] == "path"
    }
    assert parameters["portfolio_id"]["description"].startswith("Stable portfolio identifier")
    assert parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]

    foundation_catalog = spec["components"]["schemas"]["FoundationPortfolioCatalogResponse"]
    foundation_catalog_item = spec["components"]["schemas"]["FoundationPortfolioCatalogItem"]
    foundation_workspace = spec["components"]["schemas"]["FoundationWorkspaceResponse"]
    foundation_identity = spec["components"]["schemas"]["FoundationPortfolioIdentity"]
    foundation_summary = spec["components"]["schemas"]["FoundationPortfolioSummary"]
    foundation_allocation = spec["components"]["schemas"]["FoundationAllocationBucket"]
    foundation_top_position = spec["components"]["schemas"]["FoundationTopPosition"]
    foundation_performance = spec["components"]["schemas"]["FoundationPerformanceSummary"]
    foundation_rebalance = spec["components"]["schemas"]["FoundationRebalanceSummary"]
    foundation_readiness = spec["components"]["schemas"]["FoundationWorkspaceReadiness"]
    foundation_reporting = spec["components"]["schemas"]["FoundationReportingReadiness"]
    foundation_workflow_cue = spec["components"]["schemas"]["FoundationWorkflowLaunchCue"]
    foundation_evidence = spec["components"]["schemas"]["FoundationEvidenceSummary"]
    foundation_partial_failure = spec["components"]["schemas"]["FoundationPartialFailure"]

    assert foundation_catalog["properties"]["correlation_id"]["description"]
    assert foundation_catalog["properties"]["contract_version"]["description"]
    assert foundation_catalog["properties"]["items"]["description"]
    assert foundation_catalog["properties"]["items"]["examples"]
    assert foundation_catalog["properties"]["items"]["examples"][0][0]["client_id"] == "CIF_1001"
    assert (
        foundation_catalog["properties"]["items"]["examples"][0][0]["booking_center_code"] == "SG"
    )
    assert foundation_catalog_item["properties"]["portfolio_id"]["description"]
    assert foundation_catalog_item["properties"]["display_name"]["description"]
    assert foundation_catalog_item["properties"]["base_currency"]["description"]
    assert foundation_catalog_item["properties"]["client_id"]["description"]
    assert foundation_catalog_item["properties"]["booking_center_code"]["description"]
    assert foundation_workspace["properties"]["correlation_id"]["description"]
    assert foundation_workspace["properties"]["contract_version"]["description"]
    assert foundation_workspace["properties"]["as_of_date"]["description"]
    assert foundation_workspace["properties"]["portfolio"]["description"]
    assert foundation_workspace["properties"]["summary"]["description"]
    assert foundation_workspace["properties"]["allocations"]["description"]
    assert foundation_workspace["properties"]["allocations"]["examples"]
    assert foundation_workspace["properties"]["top_positions"]["description"].startswith(
        "Largest holdings ranked"
    )
    assert foundation_workspace["properties"]["top_positions"]["examples"]
    assert foundation_workspace["properties"]["performance"]["description"]
    assert foundation_workspace["properties"]["rebalance"]["description"]
    assert foundation_workspace["properties"]["readiness"]["description"]
    assert foundation_workspace["properties"]["workflow_cues"]["description"]
    assert foundation_workspace["properties"]["workflow_cues"]["examples"]
    assert foundation_workspace["properties"]["evidence"]["description"].startswith(
        "Advisor-facing evidence posture"
    )
    assert foundation_workspace["properties"]["warnings"]["description"]
    assert foundation_workspace["properties"]["partial_failures"]["description"]
    assert foundation_workspace["properties"]["partial_failures"]["examples"]
    assert foundation_identity["properties"]["portfolio_id"]["description"]
    assert foundation_identity["properties"]["display_name"]["description"]
    assert foundation_identity["properties"]["client_id"]["description"]
    assert foundation_identity["properties"]["base_currency"]["description"]
    assert foundation_identity["properties"]["booking_center_code"]["description"]
    assert foundation_summary["properties"]["market_value_base"]["description"]
    assert foundation_summary["properties"]["total_cash_base"]["description"]
    assert foundation_summary["properties"]["cash_weight_pct"]["description"]
    assert foundation_summary["properties"]["position_count"]["description"]
    assert foundation_allocation["properties"]["asset_class"]["description"]
    assert foundation_allocation["properties"]["position_count"]["description"]
    assert foundation_allocation["properties"]["market_value_base"]["description"]
    assert foundation_allocation["properties"]["weight_pct"]["description"]
    assert foundation_top_position["properties"]["security_id"]["description"]
    assert foundation_top_position["properties"]["display_name"]["description"]
    assert foundation_top_position["properties"]["asset_class"]["description"]
    assert foundation_top_position["properties"]["market_value_base"]["description"]
    assert foundation_top_position["properties"]["weight_pct"]["description"]
    assert foundation_performance["properties"]["period"]["description"]
    assert foundation_performance["properties"]["return_pct"]["description"]
    assert foundation_rebalance["properties"]["status"]["description"]
    assert foundation_rebalance["properties"]["last_run_at_utc"]["description"]
    assert foundation_rebalance["properties"]["last_rebalance_run_id"]["description"]
    assert foundation_readiness["properties"]["has_positions"]["description"]
    assert foundation_readiness["properties"]["reporting"]["description"]
    assert foundation_reporting["properties"]["status"]["description"]
    assert foundation_reporting["properties"]["generated_at_utc"]["description"]
    assert foundation_reporting["properties"]["row_count"]["description"]
    assert foundation_workflow_cue["properties"]["key"]["description"]
    assert foundation_workflow_cue["properties"]["label"]["description"]
    assert foundation_workflow_cue["properties"]["href"]["description"]
    assert foundation_evidence["properties"]["status"]["description"]
    assert foundation_evidence["properties"]["summary"]["description"]
    assert foundation_evidence["properties"]["warning_count"]["description"]
    assert foundation_evidence["properties"]["partial_failure_count"]["description"]
    assert foundation_evidence["properties"]["affected_sources"]["description"]
    assert foundation_partial_failure["properties"]["source_service"]["description"]
    assert foundation_partial_failure["properties"]["error_code"]["description"]
    assert foundation_partial_failure["properties"]["detail"]["description"]
