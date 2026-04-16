from fastapi.testclient import TestClient

from app.contracts.portfolio import (
    PortfolioActivitySummaryResponse,
    PortfolioAllocationResponse,
    PortfolioBookResponse,
    PortfolioIncomeSummaryResponse,
    PortfolioLiquidityResponse,
    PortfolioPerformanceSnapshotResponse,
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
        performance={"period": "YTD", "return_pct": 2.5},
        rebalance={
            "status": "PENDING_REVIEW",
            "last_run_at_utc": "2026-03-27T12:00:00Z",
            "last_rebalance_run_id": "rr_100",
        },
        reporting={"status": "READY", "row_count": 3},
    )
    assert payload.summary.assets_under_management_base == 1000.0
    assert payload.performance is not None
    assert payload.performance.return_pct == 2.5
    assert payload.rebalance is not None
    assert payload.rebalance.last_rebalance_run_id == "rr_100"
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
        pricing={
            "status": "Pending",
            "reasons": [
                {
                    "code": "pricing_not_published",
                    "detail": "Pricing has not yet been published for the requested date.",
                }
            ],
        },
        blocking_reasons=[
            {
                "code": "awaiting_pricing",
                "detail": "Reporting remains blocked until pricing is published.",
            }
        ],
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
    assert readiness.pricing is not None
    assert readiness.pricing.reasons[0].code == "pricing_not_published"
    assert readiness.blocking_reasons[0].code == "awaiting_pricing"
    assert workflow.actions[0].recommended is True


def test_portfolio_performance_snapshot_contract_shape() -> None:
    payload = PortfolioPerformanceSnapshotResponse(
        correlation_id="corr-10",
        portfolio_id="PF_1001",
        as_of_date="2026-03-27",
        period="YTD",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
        portfolio_return_pct=15.1,
        benchmark_return_pct=14.72,
        excess_return_pct=0.38,
        sparkline=[
            {
                "as_of_date": "2026-01-31",
                "portfolio_return_pct": 2.0,
                "benchmark_return_pct": 1.8,
                "excess_return_pct": 0.2,
            }
        ],
    )
    assert payload.benchmark_code == "BMK_GLOBAL_BALANCED_60_40"
    assert payload.sparkline[0].benchmark_return_pct == 1.8
    assert payload.unavailable is None


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
    assert "/api/v1/portfolio/portfolios/{portfolio_id}/performance-snapshot" in spec["paths"]
    workspace_schema = spec["components"]["schemas"]["PortfolioWorkspaceResponse"]
    performance_schema = spec["components"]["schemas"]["PortfolioPerformanceSummary"]
    rebalance_schema = spec["components"]["schemas"]["PortfolioRebalanceSummary"]
    readiness_schema = spec["components"]["schemas"]["PortfolioReadinessResponse"]
    readiness_indicator_schema = spec["components"]["schemas"]["PortfolioReadinessIndicator"]
    insights_schema = spec["components"]["schemas"]["PortfolioInsightsResponse"]
    insight_item_schema = spec["components"]["schemas"]["PortfolioInsight"]
    exception_item_schema = spec["components"]["schemas"]["PortfolioExceptionSummary"]
    liquidity_schema = spec["components"]["schemas"]["PortfolioLiquidityResponse"]
    projected_cashflow_schema = spec["components"]["schemas"]["PortfolioProjectedCashflowResponse"]
    allocation_schema = spec["components"]["schemas"]["PortfolioAllocationResponse"]
    positions_schema = spec["components"]["schemas"]["PortfolioPositionBookResponse"]
    transactions_schema = spec["components"]["schemas"]["PortfolioTransactionLedgerResponse"]
    income_schema = spec["components"]["schemas"]["PortfolioIncomeSummaryResponse"]
    activity_schema = spec["components"]["schemas"]["PortfolioActivitySummaryResponse"]
    book_schema = spec["components"]["schemas"]["PortfolioBookResponse"]
    workflow_schema = spec["components"]["schemas"]["PortfolioWorkflowResponse"]
    workflow_action_schema = spec["components"]["schemas"]["PortfolioWorkflowAction"]
    allocation_look_through_schema = spec["components"]["schemas"][
        "PortfolioAllocationLookThroughCapability"
    ]
    performance_snapshot_path = spec["paths"][
        "/api/v1/portfolio/portfolios/{portfolio_id}/performance-snapshot"
    ]["get"]
    performance_snapshot_period_parameter = next(
        parameter
        for parameter in performance_snapshot_path["parameters"]
        if parameter["name"] == "period"
    )
    performance_snapshot_schema = spec["components"]["schemas"][
        "PortfolioPerformanceSnapshotResponse"
    ]
    performance_snapshot_point_schema = spec["components"]["schemas"][
        "PortfolioPerformanceSnapshotPoint"
    ]
    performance_snapshot_unavailable_schema = spec["components"]["schemas"][
        "PortfolioPerformanceSnapshotUnavailable"
    ]
    cashflow_outlook_schema = spec["components"]["schemas"]["PortfolioCashflowOutlook"]
    cashflow_point_schema = spec["components"]["schemas"]["PortfolioCashflowPoint"]
    transactions_path = spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/transactions"][
        "get"
    ]
    workflow_path = spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/workflow"]["get"]
    allocations_path = spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/allocations"][
        "get"
    ]
    positions_path = spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/positions"]["get"]
    income_path = spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/income-summary"]["get"]
    activity_path = spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/activity-summary"][
        "get"
    ]
    transaction_parameters = {
        parameter["name"]: parameter for parameter in transactions_path["parameters"]
    }
    workflow_parameters = {
        parameter["name"]: parameter for parameter in workflow_path["parameters"]
    }
    allocation_parameters = {
        parameter["name"]: parameter for parameter in allocations_path["parameters"]
    }
    position_parameters = {
        parameter["name"]: parameter for parameter in positions_path["parameters"]
    }
    income_parameters = {parameter["name"]: parameter for parameter in income_path["parameters"]}
    activity_parameters = {
        parameter["name"]: parameter for parameter in activity_path["parameters"]
    }
    assert workspace_schema["properties"]["performance"]["description"]
    assert workspace_schema["properties"]["rebalance"]["description"]
    assert performance_schema["properties"]["period"]["description"]
    assert rebalance_schema["properties"]["status"]["description"]
    assert readiness_schema["properties"]["blocking_reasons"]["description"]
    assert readiness_schema["properties"]["indicators"]["description"]
    assert readiness_indicator_schema["properties"]["status"]["description"]
    assert spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/insights"]["get"][
        "description"
    ]
    assert insights_schema["properties"]["insights"]["description"]
    assert insights_schema["properties"]["exception_summaries"]["description"]
    assert insight_item_schema["properties"]["severity"]["description"]
    assert exception_item_schema["properties"]["tone"]["description"]
    assert spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/book"]["get"]["description"]
    assert spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/liquidity"]["get"][
        "description"
    ]
    assert spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/projected-cashflow"]["get"][
        "description"
    ]
    assert spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/allocations"]["get"][
        "description"
    ]
    assert spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/positions"]["get"][
        "description"
    ]
    assert transactions_path["description"]
    assert spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/income-summary"]["get"][
        "description"
    ]
    assert spec["paths"]["/api/v1/portfolio/portfolios/{portfolio_id}/activity-summary"]["get"][
        "description"
    ]
    assert book_schema["properties"]["positions"]["description"]
    assert book_schema["properties"]["allocation_views"]["description"]
    assert liquidity_schema["properties"]["cash_balances"]["description"]
    assert liquidity_schema["properties"]["warnings"]["description"]
    assert liquidity_schema["properties"]["cashflow_outlook"]["description"]
    assert projected_cashflow_schema["properties"]["cashflow_outlook"]["description"]
    assert projected_cashflow_schema["properties"]["warnings"]["description"]
    assert projected_cashflow_schema["properties"]["partial_failures"]["description"]
    assert cashflow_outlook_schema["properties"]["as_of_date"]["description"]
    assert cashflow_outlook_schema["properties"]["range_end_date"]["description"]
    assert cashflow_outlook_schema["properties"]["total_net_cashflow_base"]["description"]
    assert cashflow_outlook_schema["properties"]["projection_days"]["description"]
    assert cashflow_outlook_schema["properties"]["include_projected"]["description"]
    assert cashflow_outlook_schema["properties"]["notes"]["description"]
    assert cashflow_outlook_schema["properties"]["upcoming_points"]["description"]
    assert cashflow_point_schema["properties"]["projection_date"]["description"]
    assert cashflow_point_schema["properties"]["net_cashflow_base"]["description"]
    assert cashflow_point_schema["properties"]["projected_cumulative_cashflow_base"]["description"]
    assert allocation_schema["properties"]["reporting_currency"]["description"]
    assert allocation_schema["properties"]["look_through"]["description"]
    assert allocation_schema["properties"]["views"]["description"]
    assert allocation_parameters["reporting_currency"]["description"]
    assert allocation_parameters["look_through_mode"]["description"]
    assert allocation_look_through_schema["properties"]["requested_mode"]["description"]
    assert allocation_look_through_schema["properties"]["effective_mode"]["description"]
    assert allocation_look_through_schema["properties"]["applied"]["description"]
    assert position_parameters["include_projected"]["description"]
    assert position_parameters["reporting_currency"]["description"]
    assert positions_schema["properties"]["top_positions"]["description"]
    assert positions_schema["properties"]["positions"]["description"]
    assert transactions_schema["properties"]["include_projected"]["description"]
    assert transactions_schema["properties"]["transactions"]["description"]
    assert transaction_parameters["instrument_id"]["description"]
    assert transaction_parameters["component_type"]["description"]
    assert transaction_parameters["linked_transaction_group_id"]["description"]
    assert transaction_parameters["fx_contract_id"]["description"]
    assert transaction_parameters["swap_event_id"]["description"]
    assert transaction_parameters["near_leg_group_id"]["description"]
    assert transaction_parameters["far_leg_group_id"]["description"]
    assert transaction_parameters["sort_by"]["description"]
    assert transaction_parameters["sort_order"]["description"]
    assert income_schema["properties"]["reporting_currency"]["description"]
    assert income_schema["properties"]["totals_requested_window"]["description"]
    assert income_schema["properties"]["income_types"]["description"]
    assert income_parameters["as_of_date"]["description"]
    assert income_parameters["start_date"]["description"]
    assert income_parameters["end_date"]["description"]
    assert income_parameters["reporting_currency"]["description"]
    assert activity_schema["properties"]["reporting_currency"]["description"]
    assert activity_schema["properties"]["buckets"]["description"]
    assert activity_parameters["as_of_date"]["description"]
    assert activity_parameters["start_date"]["description"]
    assert activity_parameters["end_date"]["description"]
    assert activity_parameters["reporting_currency"]["description"]
    assert workflow_path["description"]
    assert workflow_parameters["as_of_date"]["description"]
    assert workflow_schema["properties"]["actions"]["description"]
    assert workflow_action_schema["properties"]["sequence"]["description"]
    assert workflow_action_schema["properties"]["title"]["description"]
    assert workflow_action_schema["properties"]["impact"]["description"]
    assert workflow_action_schema["properties"]["target"]["description"]
    assert workflow_action_schema["properties"]["href"]["description"]
    assert workflow_action_schema["properties"]["cta_label"]["description"]
    assert workflow_action_schema["properties"]["recommended"]["description"]
    assert performance_snapshot_path["description"]
    assert performance_snapshot_period_parameter["description"]
    assert performance_snapshot_schema["properties"]["portfolio_id"]["description"]
    assert performance_snapshot_schema["properties"]["benchmark_return_pct"]["description"]
    assert performance_snapshot_schema["properties"]["sparkline"]["description"]
    assert performance_snapshot_schema["properties"]["unavailable"]["description"]
    assert performance_snapshot_point_schema["properties"]["portfolio_return_pct"]["description"]
    assert performance_snapshot_unavailable_schema["properties"]["requirements