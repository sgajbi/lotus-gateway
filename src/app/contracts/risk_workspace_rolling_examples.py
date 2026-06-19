from typing import Any

RISK_ROLLING_PAYLOAD_EXAMPLE: dict[str, Any] = {
    "periods": [
        {
            "key": "YTD",
            "label": "YTD",
            "start_date": "2026-01-01",
            "end_date": "2026-04-04",
            "series_count": 66,
            "benchmark_series_count": 66,
            "aligned_benchmark_series_count": 64,
            "risk_free_series_count": 65,
            "aligned_risk_free_series_count": 0,
            "window_lengths_requested": [21, 63, 126, 252],
            "window_count_requested": 4,
            "window_lengths_emitted": [21, 63, 126, 252],
            "window_count_emitted": 4,
            "benchmark_context": {
                "requested": True,
                "available": True,
                "aligned": True,
                "reason": "APPLIED",
            },
            "risk_free_context": {
                "requested": True,
                "available": False,
                "aligned": False,
                "reason": "Risk-free series could not be aligned for rolling Sharpe.",
            },
            "window_results": [
                {
                    "window_length": 21,
                    "metric_summaries": {
                        "ROLLING_VOLATILITY": {
                            "total_point_count": 66,
                            "computed_point_count": 46,
                            "coverage_ratio": 0.697,
                            "min_observations_required": 21,
                            "warmup_point_count": 20,
                            "non_computed_point_count": 20,
                            "post_warmup_gap_point_count": 0,
                            "latest_observation_date": "2026-04-04",
                            "latest": 0.1374,
                            "average": 0.1221,
                            "minimum": 0.0913,
                            "maximum": 0.1662,
                            "p05": 0.0975,
                            "p50": 0.1218,
                            "p95": 0.1611,
                        }
                    },
                    "metric_series": None,
                    "metric_series_context": {
                        "requested": False,
                        "included": False,
                        "emitted_point_count": 0,
                        "reason": "Excluded from first paint; request include_time_series=true.",
                    },
                }
            ],
            "quality_flags": ["metric:ROLLING_BETA:benchmark_variance_zero"],
            "error": None,
        }
    ],
    "request_context": {
        "annualization_basis": 252,
        "requested_metrics": [
            "ROLLING_VOLATILITY",
            "ROLLING_BETA",
            "ROLLING_MAX_DRAWDOWN",
            "ROLLING_SHARPE",
        ],
        "window_lengths_requested": [21, 63, 126, 252],
        "window_count_requested": 4,
        "alignment_policy": "INNER_JOIN",
        "min_observations_policy": "STRICT",
        "include_time_series": False,
        "benchmark_context": {
            "requested": True,
            "requested_metrics": ["ROLLING_BETA"],
        },
        "risk_free_context": {
            "requested": True,
            "requested_metrics": ["ROLLING_SHARPE"],
        },
    },
}
