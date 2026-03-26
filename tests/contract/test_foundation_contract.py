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
                "instrument_name": "Equity 1",
                "asset_class": "Equity",
                "quantity": 10.0,
                "market_value_base": 500.0,
                "weight_pct": 50.0,
            }
        ],
        performance={"period": "YTD", "return_pct": 4.2},
        rebalance={"status": "READY"},
        readiness={"has_positions": True, "reporting": {"status": "READY", "row_count": 2}},
        workflow_cues=[
            {"key": "performance", "label": "Open Performance", "href": "/app/performance"}
        ],
    )
    assert payload.portfolio.portfolio_id == "PF_1001"
    assert payload.summary.position_count == 3
    assert payload.top_positions[0].security_id == "EQ_1"
    assert payload.readiness.reporting.status == "READY"


def test_foundation_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    assert "/api/v1/foundation/portfolios" in spec["paths"]
    assert "/api/v1/foundation/portfolios/{portfolio_id}/workspace" in spec["paths"]
