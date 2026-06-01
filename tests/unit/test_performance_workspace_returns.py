from app.services.performance_workspace_returns import (
    build_workspace_comparative_summary,
    extract_twr_workspace_block,
    resolve_results_period_key,
)


def test_extract_twr_workspace_block_returns_requested_basis_block():
    period_payload = {
        "portfolio_twr": {
            "net": {"summary": {"period_return": {"base": 4.2}}},
            "gross": {"summary": {"period_return": {"base": 4.6}}},
        }
    }

    assert extract_twr_workspace_block(period_payload, "NET") == {
        "summary": {"period_return": {"base": 4.2}}
    }
    assert extract_twr_workspace_block(period_payload, "gross") == {
        "summary": {"period_return": {"base": 4.6}}
    }


def test_extract_twr_workspace_block_fails_closed_for_invalid_payloads():
    assert extract_twr_workspace_block({"portfolio_twr": []}, "net") == {}
    assert extract_twr_workspace_block({"portfolio_twr": {"net": []}}, "net") == {}
    assert extract_twr_workspace_block({}, "net") == {}


def test_build_workspace_comparative_summary_maps_returns_and_economics():
    summary = build_workspace_comparative_summary(
        metric_basis="NET",
        portfolio_block={
            "summary": {
                "period_return": {"base": 5.4321},
                "annualized_return": {"base": 8.7654},
                "economics": {
                    "begin_market_value": 1000000,
                    "end_market_value": 1050000,
                    "beginning_cash_flow": 10000,
                    "ending_cash_flow": 5000,
                    "flow_adjusted_end_market_value": 1045000,
                    "net_cash_flow": 15000,
                    "fees": 250,
                },
            }
        },
        benchmark_block={
            "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
            "return_source": "calculated",
            "input_mode": "stateful",
            "summary": {"period_return": {"base": 4.25}},
        },
        active_basis_block={"period_return": {"base": 1.1821}},
    )

    assert summary.metric_basis == "NET"
    assert summary.portfolio_return_pct == 5.4321
    assert summary.benchmark_return_pct == 4.25
    assert summary.active_return_pct == 1.1821
    assert summary.annualized_return_pct == 8.7654
    assert summary.benchmark_id == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert summary.benchmark_return_source == "calculated"
    assert summary.benchmark_input_mode == "stateful"
    assert summary.begin_market_value == 1000000
    assert summary.end_market_value == 1050000
    assert summary.beginning_cash_flow == 10000
    assert summary.ending_cash_flow == 5000
    assert summary.flow_adjusted_end_market_value == 1045000
    assert summary.net_cash_flow == 15000
    assert summary.fees == 250


def test_build_workspace_comparative_summary_tolerates_missing_nested_blocks():
    summary = build_workspace_comparative_summary(
        metric_basis="NET",
        portfolio_block={"summary": []},
        benchmark_block={},
        active_basis_block=[],
    )

    assert summary.metric_basis == "NET"
    assert summary.portfolio_return_pct is None
    assert summary.benchmark_return_pct is None
    assert summary.active_return_pct is None
    assert summary.begin_market_value is None


def test_resolve_results_period_key_matches_case_insensitively():
    assert (
        resolve_results_period_key(
            requested_period="ytd",
            results_by_period={"MTD": {}, "YTD": {}},
        )
        == "YTD"
    )


def test_resolve_results_period_key_falls_back_to_first_available_period():
    assert (
        resolve_results_period_key(
            requested_period="EXPLICIT",
            results_by_period={"QTD": {}, "YTD": {}},
        )
        == "QTD"
    )
