from app.services.performance_workspace_summary import parse_workspace_summary_result


def test_parse_workspace_summary_result_returns_named_summary():
    warnings: list[str] = []
    partial_failures = []

    parsed = parse_workspace_summary_result(
        result=(
            200,
            {
                "results_by_period": {
                    "YTD": {
                        "benchmark": {
                            "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                            "summary": {"period_return": {"base": 2.9}},
                            "breakdowns": {
                                "monthly": [
                                    {
                                        "period": "2026-03",
                                        "period_return": {"base": 1.0},
                                        "cumulative_return": {"base": 2.9},
                                    }
                                ],
                            },
                        },
                        "active": {
                            "net": {"period_return": {"base": 0.2}},
                            "gross": {"period_return": {"base": 0.3}},
                        },
                        "portfolio_twr": {
                            "net": {
                                "summary": {
                                    "period_return": {"base": 3.1},
                                    "annualized_return": {"base": 6.3},
                                },
                                "breakdowns": {
                                    "monthly": [
                                        {
                                            "period": "2026-03",
                                            "period_return": {"base": 1.2},
                                            "cumulative_return": {"base": 3.1},
                                        }
                                    ],
                                },
                            },
                            "gross": {
                                "summary": {
                                    "period_return": {"base": 3.2},
                                    "annualized_return": {"base": 6.4},
                                },
                                "breakdowns": {
                                    "monthly": [
                                        {
                                            "period": "2026-03",
                                            "period_return": {"base": 1.3},
                                            "cumulative_return": {"base": 3.2},
                                        }
                                    ],
                                },
                            },
                        },
                        "money_weighted_return": {
                            "period_return": 3.05,
                            "input_mode": "stateful",
                        },
                        "contribution": {
                            "metric_basis": "NET",
                            "summary": {"portfolio_contribution": 3.1},
                        },
                        "attribution": {
                            "metric_basis": "NET",
                            "result": {
                                "reconciliation": {
                                    "total_active_return": 0.2,
                                    "sum_of_effects": 0.19,
                                },
                            },
                            "benchmark_context": {
                                "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                            },
                        },
                    },
                },
            },
        ),
        requested_period="YTD",
        chart_frequency="monthly",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert parsed.net_performance.portfolio_return_pct == 3.1
    assert parsed.net_performance.benchmark_return_pct == 2.9
    assert parsed.net_performance.active_return_pct == 0.2
    assert parsed.gross_performance.portfolio_return_pct == 3.2
    assert parsed.gross_performance.active_return_pct == 0.3
    assert len(parsed.net_chart) == 1
    assert parsed.net_chart[0].label == "2026-03"
    assert parsed.net_chart[0].active_return_pct == 0.2
    assert parsed.money_weighted_return is not None
    assert parsed.money_weighted_return.money_weighted_return_pct == 3.05
    assert parsed.contribution is not None
    assert parsed.contribution.portfolio_contribution_pct == 3.1
    assert parsed.attribution is not None
    assert parsed.attribution.active_return_pct == 0.2
    assert parsed.resolved_benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert warnings == []
    assert partial_failures == []


def test_parse_workspace_summary_result_records_upstream_failure():
    warnings: list[str] = []
    partial_failures = []

    parsed = parse_workspace_summary_result(
        result=(503, {"detail": "workspace summary unavailable"}),
        requested_period="YTD",
        chart_frequency="monthly",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert parsed.net_performance.metric_basis == "NET"
    assert parsed.net_performance.portfolio_return_pct is None
    assert parsed.gross_performance.metric_basis == "GROSS"
    assert parsed.net_chart == []
    assert parsed.resolved_benchmark_code is None
    assert warnings == ["PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE"]
    assert len(partial_failures) == 1
    assert partial_failures[0].source_service == "lotus-performance"
    assert partial_failures[0].error_code == "HTTP_503"
    assert partial_failures[0].detail == "workspace summary unavailable"
