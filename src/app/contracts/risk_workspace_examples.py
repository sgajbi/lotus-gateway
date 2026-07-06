from typing import Any, cast

from app.contracts.risk_workspace_attribution import _RISK_ATTRIBUTION_PAYLOAD_EXAMPLE
from app.contracts.risk_workspace_concentration import _RISK_CONCENTRATION_PAYLOAD_EXAMPLE
from app.contracts.risk_workspace_rolling_examples import RISK_ROLLING_PAYLOAD_EXAMPLE

_RISK_SUMMARY_RESPONSE_EXAMPLE: dict[str, Any] = {
    "correlation_id": "corr-risk-summary-1",
    "contract_version": "risk-workspace.v1",
    "portfolio_id": "PF_1001",
    "period": "YTD",
    "as_of_date": "2026-02-24",
    "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
    "source_service": "lotus-risk",
    "state": "partial",
    "payload": {
        "periods": [
            {
                "key": "YTD",
                "label": "YTD",
                "start_date": "2026-01-01",
                "end_date": "2026-02-24",
                "portfolio_observation_count": 37,
                "benchmark_observation_count": 37,
                "aligned_benchmark_observation_count": 36,
                "benchmark_context": {
                    "reason": "APPLIED",
                    "requested_metrics": [
                        "BETA",
                        "TRACKING_ERROR",
                        "INFORMATION_RATIO",
                    ],
                },
                "metrics": [
                    {
                        "key": "VOLATILITY",
                        "label": "Volatility",
                        "value": 0.12,
                        "state": "ready",
                        "reason": None,
                        "details": {"annualization_basis": 252},
                    },
                    {
                        "key": "SHARPE",
                        "label": "Sharpe ratio",
                        "value": None,
                        "state": "partial",
                        "reason": "Risk-free series did not align for the selected window.",
                        "details": {
                            "error": ("Risk-free series did not align for the selected window.")
                        },
                    },
                ],
            }
        ]
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
            "key": "risk_free_series",
            "label": "Risk-free series",
            "state": "partial",
            "reason": (
                "Sharpe is partial or unavailable when lotus-risk cannot source the required "
                "risk-free series."
            ),
            "source_service": "lotus-risk",
        },
    ],
    "warnings": ["RISK_SUMMARY_PARTIAL"],
    "partial_failures": [
        {
            "source_service": "lotus-risk",
            "error_code": "RISK_FREE_UNAVAILABLE",
            "detail": "Sharpe could not be produced for one or more requested periods.",
        }
    ],
    "metadata": {
        "generated_at": "2026-04-04T08:15:00Z",
        "input_mode": "stateful",
        "methodology_version": "risk-summary.v1",
        "cache_status": "miss",
    },
}

_RISK_CONCENTRATION_RESPONSE_EXAMPLE: dict[str, Any] = {
    "correlation_id": "corr-risk-concentration-1",
    "contract_version": "risk-workspace.v1",
    "portfolio_id": "PF_RISK_CONC",
    "period": "YTD",
    "as_of_date": "2026-04-04",
    "benchmark_code": "BMK_1",
    "source_service": "lotus-risk",
    "state": "partial",
    "payload": cast(Any, _RISK_CONCENTRATION_PAYLOAD_EXAMPLE),
    "supportability": [
        {
            "key": "portfolio_positions",
            "label": "Portfolio positions",
            "state": "ready",
            "reason": None,
            "source_service": "lotus-risk",
        },
        {
            "key": "issuer_enrichment",
            "label": "Issuer enrichment",
            "state": "partial",
            "reason": "Some positions could not be mapped to ultimate-parent issuer groups.",
            "source_service": "lotus-risk",
        },
        {
            "key": "issuer_grouping",
            "label": "Issuer grouping",
            "state": "ready",
            "reason": None,
            "source_service": "lotus-risk",
        },
    ],
    "warnings": ["RISK_CONCENTRATION_PARTIAL"],
    "partial_failures": [
        {
            "source_service": "lotus-risk",
            "error_code": "ISSUER_ENRICHMENT_PARTIAL",
            "detail": "One or more positions were excluded from issuer grouping enrichment.",
        }
    ],
    "metadata": {
        "generated_at": "2026-04-04T08:15:00Z",
        "input_mode": "stateful",
        "methodology_version": "risk-concentration.v1",
        "cache_status": "miss",
    },
}

_RISK_DRAWDOWN_RESPONSE_EXAMPLE: dict[str, Any] = {
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
            "state": "partial",
            "reason": (
                "Underwater path detail is only returned when the drawer request asks for it."
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

_RISK_ROLLING_RESPONSE_EXAMPLE: dict[str, Any] = {
    "correlation_id": "corr-risk-rolling-1",
    "contract_version": "risk-workspace.v1",
    "portfolio_id": "PF_RISK_ROLLING",
    "period": "YTD",
    "as_of_date": "2026-04-04",
    "benchmark_code": "BMK_1",
    "source_service": "lotus-risk",
    "state": "partial",
    "payload": cast(Any, RISK_ROLLING_PAYLOAD_EXAMPLE),
    "supportability": [
        {
            "key": "portfolio_returns",
            "label": "Portfolio returns",
            "state": "ready",
            "reason": None,
            "source_service": "lotus-risk",
        },
        {
            "key": "benchmark_returns",
            "label": "Benchmark returns",
            "state": "ready",
            "reason": None,
            "source_service": "lotus-risk",
        },
        {
            "key": "risk_free_series",
            "label": "Risk-free series",
            "state": "partial",
            "reason": (
                "Rolling Sharpe is unavailable because the risk-free series could not be sourced."
            ),
            "source_service": "lotus-risk",
        },
        {
            "key": "rolling_time_series",
            "label": "Rolling time series",
            "state": "partial",
            "reason": (
                "Rolling metric series is available on demand and excluded from first paint."
            ),
            "source_service": "lotus-risk",
        },
    ],
    "warnings": [
        "RISK_ROLLING_QUALITY_FLAGS",
        "RISK_ROLLING_SHARPE_PARTIAL",
    ],
    "partial_failures": [
        {
            "source_service": "lotus-risk",
            "error_code": "ROLLING_SHARPE_UNAVAILABLE",
            "detail": (
                "Rolling Sharpe is unavailable because the risk-free series could not be sourced."
            ),
        }
    ],
    "metadata": {
        "generated_at": "2026-04-04T08:15:00Z",
        "input_mode": "stateful",
        "methodology_version": "rolling_metrics.v1",
        "cache_status": "miss",
    },
}

_RISK_ATTRIBUTION_RESPONSE_EXAMPLE: dict[str, Any] = {
    "correlation_id": "corr-risk-attribution-1",
    "contract_version": "risk-workspace.v1",
    "portfolio_id": "PF_RISK_ATTRIBUTION",
    "period": "YTD",
    "as_of_date": "2026-04-04",
    "benchmark_code": "BMK_1",
    "source_service": "lotus-risk",
    "state": "partial",
    "payload": cast(Any, _RISK_ATTRIBUTION_PAYLOAD_EXAMPLE),
    "supportability": [
        {
            "key": "portfolio_returns",
            "label": "Portfolio returns",
            "state": "ready",
            "reason": None,
            "source_service": "lotus-risk",
        },
        {
            "key": "exposure_history",
            "label": "Exposure history",
            "state": "ready",
            "reason": None,
            "source_service": "lotus-core",
        },
        {
            "key": "benchmark_returns",
            "label": "Benchmark returns",
            "state": "ready",
            "reason": None,
            "source_service": "lotus-performance",
        },
        {
            "key": "benchmark_exposure_context",
            "label": "Benchmark exposure context",
            "state": "blocked",
            "reason": ("Benchmark issuer exposure semantics are not yet approved for active risk."),
            "source_service": "lotus-performance",
        },
    ],
    "warnings": ["RISK_ATTRIBUTION_PARTIAL"],
    "partial_failures": [
        {
            "source_service": "lotus-risk",
            "error_code": "RISK_ATTRIBUTION_PERIOD_ERROR",
            "detail": "YTD: Benchmark overlap required manual review.",
        }
    ],
    "metadata": {
        "generated_at": "2026-04-04T08:15:00Z",
        "input_mode": "stateful",
        "methodology_version": "historical_attribution.v1",
        "cache_status": "miss",
    },
}
