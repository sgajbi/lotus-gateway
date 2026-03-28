from fastapi.testclient import TestClient

from app.contracts.portfolio import (
    PortfolioActivitySummaryResponse,
    PortfolioAllocationResponse,
    PortfolioBookResponse,
    PortfolioIncomeSummaryResponse,
    PortfolioLiquidityResponse,
    PortfolioPositionBookResponse,
    PortfolioReadinessResponse,
    PortfolioWorkflowResponse,
    PortfolioWorkspaceResponse,
)
from app.main import app


def test_portfolio_workspace_contract_shape() -> None:
    payload = PortfolioWorkspaceResponse(
        correlation_id="corr-1",
        contract_version="v1",
        as_of_date="2026-03-27",
        portfolio={
            "portfolio_id": "PF_1001",
            "display_name": "PF_1001",
            "base_currency": "USD",
        },
        profile={"status": "ACTIVE"},
        summary={
            "assets_under_management_base": 1000.0,
            "invested_market_value_base": 900.0,
            "cash_market_value_base": 100.0,
            "cash_weight_pct": 10.0,
            "position_count": 3,
            "cash_balance_count": 1,
        },
        reporting={"status": "READY", "row_count": 3},
    )
    assert payload.summary.assets_under_management_base == 1000.0
    assert payload.reporting.status == "READY"


def test_portfolio_book_contract_shape() -> None:
    payload = PortfolioBookResponse(
        correlation_id="corr-2",
        contract_version="v1",
        as_of_date="2026-03-27",
        portfolio={"portfolio_id": "PF_1001", "display_name": "PF_1001", "base_currency": "USD"},
        summary={
            "assets_under_management_base": 1000.0,
            "invested_market_value_base": 900.0,
            "cash_market_value_base": 100.0,
            "cash_weight_pct": 10.0,
            "position_count": 3,
            "cash_balance_count": 1,
        },
        cash_balances=[
            {"security_id": "CASH_USD", "instrument_name": "USD Cash", "quantity": 100.0}
        ],
        positions=[{"security_id": "EQ_1", "instrument_name": "Equity 1", "quantity": 10.0}],
    )
    assert payload.positions[0].security_id == "EQ_1"


def test_portfolio_modular_contract_shapes() -> None:
    liquidity = PortfolioLiquidityResponse(
        correlation_id="corr-3",
        contract_version="v1",
        portfolio_id="PF_1001",
        as_of_date="2026-03-27",
        summary={
            "assets_under_management_base": 1000.0,
            "invested_market_value_base": 900.0,
            "cash_market_value_base": 100.0,
            "cash_weight_pct": 10.0,
            "position_count": 3,
            "cash_balance_count": 1,
        },
        cash_balances=[
            {"security_id": "CASH_USD", "instrument_name": "USD Cash", "quantity": 100.0}
        ],
    )
    allocations = PortfolioAllocationResponse(
        correlation_id="corr-4",
        contract_version="v1",
        portfolio_id="PF_1001",
        as_of_date="2026-03-27",
        summary=liquidity.summary.model_dump(),
        views=[
            {
                "dimension": "asset_class",
                "buckets": [{"bucket": "Equity", "position_count": 1}],
            }
        ],
    )
    positions = PortfolioPositionBookResponse(
        correlation_id="corr-5",
        contract_version="v1",
        portfolio_id="PF_1001",
        as_of_date="2026-03-27",
        summary=liquidity.summary.model_dump(),
        positions=[{"security_id": "EQ_1", "instrument_name": "Equity 1", "quantity": 10.0}],
    )
    assert liquidity.cash_balances[0].security_id == "CASH_USD"
    assert allocations.views[0].dimension == "asset_class"
    assert positions.positions[0].security_id == "EQ_1"


def test_portfolio_reporting_contract_shapes() -> None:
    income = PortfolioIncomeSummaryResponse(
        correlation_id="corr-6",
        portfolio_id="PF_1001",
        reporting_currency="USD",
        window_start_date="2026-03-01",
        window_end_date="2026-03-27",
        totals_requested_window={
            "gross": {"reporting_currency_amount": 20.0, "transaction_count": 1},
            "withholding_tax": {"reporting_currency_amount": 2.0, "transaction_count": 1},
            "other_deductions": {"reporting_currency_amount": 0.0, "transaction_count": 1},
            "net": {"reporting_currency_amount": 18.0, "transaction_count": 1},
        },
        totals_year_to_date={
            "gross": {"reporting_currency_amount": 40.0, "transaction_count": 2},
            "withholding_tax": {"reporting_currency_amount": 4.0, "transaction_count": 2},
            "other_deductions": {"reporting_currency_amount": 0.0, "transaction_count": 2},
            "net": {"reporting_currency_amount": 36.0, "transaction_count": 2},
        },
        income_types=[
            {
                "income_type": "DIVIDEND",
                "requested_window": {
                    "gross": {"reporting_currency_amount": 20.0, "transaction_count": 1},
                    "withholding_tax": {
                        "reporting_currency_amount": 2.0,
                        "transaction_count": 1,
                    },
                    "other_deductions": {
                        "reporting_currency_amount": 0.0,
                        "transaction_count": 1,
                    },
                    "net": {"reporting_currency_amount": 18.0, "transaction_count": 1},
                },
                "year_to_date": {
                    "gross": {"reporting_currency_amount": 40.0, "transaction_count": 2},
                    "withholding_tax": {
                        "reporting_currency_amount": 4.0,
                        "transaction_count": 2,
                    },
                    "other_deductions": {
                        "reporting_currency_amount": 0.0,
                        "transaction_count": 2,
                    },
                    "net": {"reporting_currency_amount": 36.0, "transaction_count": 2},
                },
            }
        ],
    )
    activity = PortfolioActivitySummaryResponse(
        correlation_id="corr-7",
        portfolio_id="PF_1001",
        reporting_currency="USD",
        window_start_date="2026-03-01",
        window_end_date="2026-03-27",
        buckets=[
            {
                "bucket": "INFLOWS",
                "requested_window": {"reporting_currency_amount": 100.0, "transaction_count": 1},
                "year_to_date": {"reporting_currency_amount": 150.0, "transaction_count": 2},
            }
        ],
    )
    assert income.income_types[0].income_type == "DIVIDEND"
    assert activity.buckets[0].bucket == "INFLOWS"


def test_portfolio_readiness_and_workflow_contract_shapes() -> None:
    readiness = PortfolioReadinessResponse(
        correlation_id="corr-8",
        portfolio_id="PF_1001",
        as_of_date="2026-03-27",
        indicators=[
            {
                "key": "holdings",
                "label": "Holdings",
                "status": "Ready",
                "href": "#portfolio-insights",
            }
        ],
    )
    workflow = PortfolioWorkflowResponse(
        correlation_id="corr-9",
        portfolio_id="PF_1001",
        as_of_date="2026-03-27",
        actions=[
            {
                "sequence": 1,
                "title": "Review performance",
                "impact": "Review portfolio return once the book is valued.",
                "target": "Target: Performance workflow for this portfolio",
                "href": "/performance?portfolioId=PF_1001",
                "cta_label": "Performance",
                "recommended": True,
            }
        ],
    )
    assert readiness.indicators[0].key == "holdings"
    assert workflow.actions[0].recommended is True


def test_portfolio_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    assert "/api/v1/portfolio/portfolios" in spec["paths"]
    assert "/api/v1/portfolio/portfolios/{portfolio_id}/workspace" in spec["paths"]
    assert "/api/v1/portfolio/portfolios/{portfolio_id}/book" in spec["paths"]
    assert "/api/v1/portfolio/portfolios/{portfolio_id}/liquidity" in spec["paths"]
    assert "/api/v1/portfolio/portfolios/{portfolio_id}/allocations" in spec["paths"]
    assert "/api/v1/portfolio/portfolios/{portfolio_id}/positions" in spec["paths"]
    assert "/api/v1/portfolio/portfolios/{portfolio_id}/income-summary" in spec["paths"]
    assert "/api/v1/portfolio/portfolios/{portfolio_id}/activity-summary" in spec["paths"]
    assert "/api/v1/portfolio/portfolios/{portfolio_id}/transactions" in spec["paths"]
    assert "/api/v1/portfolio/portfolios/{portfolio_id}/readiness" in spec["paths"]
    assert "/api/v1/portfolio/portfolios/{portfolio_id}/workflow" in spec["paths"]
