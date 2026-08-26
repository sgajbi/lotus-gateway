"""Static OpenAPI example fragments for performance workspace details."""

PERFORMANCE_WORKSPACE_DETAILS_EXAMPLE_DETAILS = {
    "net_chart": [
        {
            "label": "2026-01",
            "frequency": "monthly",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "portfolio_return_pct": 2.2,
            "benchmark_return_pct": 1.9,
            "active_return_pct": 0.3,
            "cumulative_portfolio_return_pct": 2.2,
            "cumulative_benchmark_return_pct": 1.9,
            "cumulative_active_return_pct": 0.3,
        }
    ],
    "gross_chart": [
        {
            "label": "2026-01",
            "frequency": "monthly",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "portfolio_return_pct": 2.4,
            "benchmark_return_pct": 2.0,
            "active_return_pct": 0.4,
            "cumulative_portfolio_return_pct": 2.4,
            "cumulative_benchmark_return_pct": 2.0,
            "cumulative_active_return_pct": 0.4,
        }
    ],
    "contribution": {
        "metric_basis": "NET",
        "weighting_scheme": "average_weight",
        "portfolio_contribution_pct": 5.42,
        "total_portfolio_return_pct": 5.42,
        "coverage_mv_pct": 98.7,
        "portfolio_local_contribution_pct": 4.8,
        "portfolio_fx_contribution_pct": 0.62,
        "position_rows": [
            {
                "position_id": "AAPL",
                "contribution_pct": 1.55,
                "weight_avg_pct": 24.1,
                "total_return_pct": 8.2,
                "local_contribution_pct": 1.18,
                "fx_contribution_pct": 0.37,
            }
        ],
        "levels": [
            {
                "level": 1,
                "name": "asset_class",
                "total_contribution_pct": 5.0,
                "total_weight_avg_pct": 100.0,
                "total_portfolio_return_pct": 5.42,
                "rows": [
                    {
                        "key_label": "Equity",
                        "contribution_pct": 3.8,
                        "weight_avg_pct": 61.0,
                        "total_return_pct": 7.4,
                        "local_contribution_pct": 3.4,
                        "fx_contribution_pct": 0.4,
                        "is_other": False,
                    }
                ],
            }
        ],
    },
    "attribution": {
        "metric_basis": "NET",
        "model": "BF",
        "linking": "carino",
        "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
        "benchmark_return_source": "calculated",
        "active_return_pct": 0.52,
        "sum_of_effects_pct": 0.5,
        "residual_pct": 0.02,
        "levels": [
            {
                "dimension": "asset_class",
                "allocation_total_pct": 0.18,
                "selection_total_pct": 0.24,
                "interaction_total_pct": 0.03,
                "total_effect_pct": 0.45,
                "rows": [
                    {
                        "key_label": "Equity",
                        "portfolio_weight_avg_pct": 61.0,
                        "benchmark_weight_avg_pct": 58.0,
                        "portfolio_return_pct": 7.4,
                        "benchmark_return_pct": 6.8,
                        "allocation_pct": 0.18,
                        "selection_pct": 0.24,
                        "interaction_pct": 0.03,
                        "total_effect_pct": 0.45,
                    }
                ],
            }
        ],
    },
    "warnings": ["PERFORMANCE_DETAILS_CURRENCY_NOT_APPLIED_BASE"],
    "partial_failures": [],
}
