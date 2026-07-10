from typing import Any

RISK_DRAWDOWN_RESPONSE_EXAMPLE: dict[str, Any] = {
    "correlation_id": "corr-risk-drawdown-1",
    "contract_version": "risk-workspace.v1",
    "portfolio_id": "PF_RISK_DRAWDOWN",
    "period": "YTD",
    "as_of_date": "2026-04-04",
    "benchmark_code": "BMK_1",
    "source_service": "lotus-risk",
    "state": "partial",
    "payload": {
        "periods": [
            {
                "key": "YTD",
                "label": "YTD",
                "start_date": "2026-01-01",
                "end_date": "2026-04-04",
                "portfolio_observation_count": 65,
                "benchmark_observation_count": 65,
                "summary": {
                    "max_drawdown": -0.124533,
                    "max_drawdown_peak_date": "2026-01-12",
                    "max_drawdown_trough_date": "2026-02-03",
                    "max_drawdown_recovery_date": None,
                    "is_recovered": False,
                    "days_to_trough": 16,
                    "days_to_recovery": None,
                    "time_under_water_days": 34,
                    "average_drawdown": -0.041208,
                    "ulcer_index": 0.053901,
                    "drawdown_at_risk_95": -0.101552,
                    "conditional_drawdown_at_risk_95": -0.117884,
                },
                "episodes": [
                    {
                        "episode_id": "dd_0001",
                        "peak_date": "2026-01-12",
                        "trough_date": "2026-02-03",
                        "recovery_date": None,
                        "depth": -0.124533,
                        "days_to_trough": 16,
                        "days_to_recovery": None,
                        "total_days": 34,
                        "is_recovered": False,
                    }
                ],
                "relative_to_benchmark": {
                    "max_drawdown": -0.0821,
                    "max_drawdown_peak_date": "2026-01-11",
                    "max_drawdown_trough_date": "2026-02-01",
                    "max_drawdown_recovery_date": None,
                    "is_recovered": False,
                    "days_to_trough": 15,
                    "days_to_recovery": None,
                    "time_under_water_days": 31,
                },
                "relative_to_benchmark_context": {
                    "requested": True,
                    "applied": True,
                    "reason": "APPLIED",
                    "aligned_observation_count": 63,
                },
                "underwater_series": None,
                "error": None,
            }
        ],
        "analysis_context": {
            "include_underwater_series": False,
            "include_episode_list": True,
            "top_n_episodes": 5,
            "cdar_alpha": 0.95,
            "minimum_episode_depth_bps": 0.0,
            "duration_unit": "BUSINESS_DAYS",
            "include_benchmark": True,
            "missing_benchmark_policy": "IGNORE",
        },
    },
    "supportability": [
        {
            "key": "portfolio_returns",
            "label": "Portfolio returns",
            "state": "ready",
            "reason": None,
            "source_service": "lotus-risk",
        },
        {
            "key": "benchmark_relative_drawdown",
            "label": "Benchmark-relative drawdown",
            "state": "partial",
            "reason": "Benchmark-relative drawdown was not returned by lotus-risk.",
            "source_service": "lotus-risk",
        },
        {
            "key": "underwater_series",
            "label": "Underwater series",
            "state": "ready",
            "reason": (
                "Underwater path detail is only returned when the drawdown request asks for it."
            ),
            "source_service": "lotus-risk",
        },
    ],
    "warnings": ["RISK_DRAWDOWN_PARTIAL"],
    "partial_failures": [
        {
            "source_service": "lotus-risk",
            "error_code": "BENCHMARK_RELATIVE_DRAWDOWN_UNAVAILABLE",
            "detail": (
                "Benchmark-relative drawdown was not returned for one or more requested periods."
            ),
        }
    ],
    "metadata": {
        "generated_at": "2026-04-04T08:15:00Z",
        "input_mode": "stateful",
        "methodology_version": "drawdown.v1",
        "cache_status": "miss",
    },
}

RISK_DRAWDOWN_PAYLOAD_SCHEMA_EXAMPLE: dict[str, Any] = {
    **RISK_DRAWDOWN_RESPONSE_EXAMPLE["payload"],
    "periods": [
        {
            **RISK_DRAWDOWN_RESPONSE_EXAMPLE["payload"]["periods"][0],
            "underwater_series": [
                {"date": "2026-01-20", "drawdown": -0.0521},
                {"date": "2026-01-21", "drawdown": -0.061},
            ],
        }
    ],
    "analysis_context": {
        **RISK_DRAWDOWN_RESPONSE_EXAMPLE["payload"]["analysis_context"],
        "include_underwater_series": True,
    },
}
