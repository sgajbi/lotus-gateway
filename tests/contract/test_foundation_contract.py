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
    workspace_operation = spec["paths"]["/api/v1/foundation/portfolios/{portfolio_id}/workspace"][
        "get"
    ]
    assert "top positions" in workspace_operation["description"].lower()
    foundation_workspace = spec["components"]["schemas"]["FoundationWorkspaceResponse"]
    assert foundation_workspace["properties"]["top_positions"]["description"].startswith(
        "Largest holdings ranked"
    )
    assert foundation_workspace["properties"]["evidence"]["description"].startswith(
        "Advisor-facing evidence posture"
    )
