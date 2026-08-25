from typing import Any, cast

from app.contracts.risk_workspace_attribution_examples import (
    RISK_ATTRIBUTION_PAYLOAD_EXAMPLE as _RISK_ATTRIBUTION_PAYLOAD_EXAMPLE,
)
from app.contracts.risk_workspace_concentration_examples import (
    RISK_CONCENTRATION_PAYLOAD_EXAMPLE as _RISK_CONCENTRATION_PAYLOAD_EXAMPLE,
)
from app.contracts.risk_workspace_drawdown_examples import RISK_DRAWDOWN_RESPONSE_EXAMPLE
from app.contracts.risk_workspace_rolling_examples import RISK_ROLLING_PAYLOAD_EXAMPLE

_MANDATE_COMPARISON_COMMON: dict[str, Any] = {
    "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
    "mandate_version": "3",
    "mandate_as_of_date": "2026-02-24",
    "risk_profile": "BALANCED",
    "comparison_as_of_date": "2026-02-24",
    "mandate_health_as_of_date": "2026-02-24",
    "date_alignment_state": "aligned",
    "review_policy": {
        "review_frequency": "QUARTERLY",
        "last_review_date": "2025-12-31",
        "next_review_due_date": "2026-03-31",
        "state": "scheduled",
    },
    "source_lineage": [
        {
            "product_name": "DiscretionaryMandateBinding",
            "product_version": "v1",
            "source_system": "lotus-core",
            "source_record_id": "DiscretionaryMandateBinding:v1",
            "data_quality_status": "COMPLETE",
            "latest_evidence_timestamp": "2026-02-24T01:00:00Z",
        }
    ],
    "supportability": {
        "state": "ready",
        "reason": None,
        "source_service": "lotus-manage",
    },
}

_SUMMARY_MANDATE_COMPARISON_EXAMPLE: dict[str, Any] = {
    **_MANDATE_COMPARISON_COMMON,
    "constraints": [
        {
            "key": "cash_band",
            "label": "Cash allocation",
            "limit": {
                "minimum": 0.02,
                "maximum": 0.10,
                "unit": "ratio",
                "source_service": "lotus-manage",
            },
            "measure": {
                "value": 0.0859,
                "unit": "ratio",
                "basis": None,
                "as_of_date": "2026-02-24",
                "source_service": "lotus-core",
                "source_metric": "cash_weight",
            },
            "headroom": 0.0141,
            "state": "within",
            "reason": "Cash allocation is within the approved mandate band.",
            "source_state": "READY",
            "source_reason_code": "CASH_LIQUIDITY_READY",
        },
        {
            "key": "max_tracking_error",
            "label": "Tracking error",
            "limit": None,
            "measure": {
                "value": 0.04,
                "unit": "ratio",
                "basis": None,
                "as_of_date": "2026-02-24",
                "source_service": "lotus-risk",
                "source_metric": "TRACKING_ERROR",
            },
            "headroom": None,
            "state": "not_defined",
            "reason": "The mandate does not define a tracking error limit.",
            "source_state": None,
            "source_reason_code": None,
        },
    ],
}

_CONCENTRATION_MANDATE_COMPARISON_EXAMPLE: dict[str, Any] = {
    **_MANDATE_COMPARISON_COMMON,
    "constraints": [
        {
            "key": "single_position_max_weight",
            "label": "Largest position exposure",
            "limit": {
                "minimum": None,
                "maximum": 0.20,
                "unit": "ratio",
                "source_service": "lotus-manage",
            },
            "measure": {
                "value": 0.1897,
                "unit": "ratio",
                "basis": "total_market_value_base",
                "as_of_date": "2026-02-24",
                "source_service": "lotus-risk",
                "source_metric": "top_position_weight_current",
            },
            "headroom": 0.0103,
            "state": "within",
            "reason": "Largest position exposure is within the approved mandate limit.",
            "source_state": None,
            "source_reason_code": None,
        },
        {
            "key": "issuer_max_weight",
            "label": "Largest issuer exposure",
            "limit": {
                "minimum": None,
                "maximum": 0.20,
                "unit": "ratio",
                "source_service": "lotus-manage",
            },
            "measure": {
                "value": 0.2107,
                "unit": "ratio",
                "basis": "total_market_value_base",
                "as_of_date": "2026-02-24",
                "source_service": "lotus-risk",
                "source_metric": "top_issuer_weight_current",
            },
            "headroom": -0.0107,
            "state": "breach",
            "reason": "Largest issuer exposure exceeds the approved mandate limit.",
            "source_state": None,
            "source_reason_code": None,
        },
    ],
}

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
    "mandate_comparison": _SUMMARY_MANDATE_COMPARISON_EXAMPLE,
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
    "mandate_comparison": _CONCENTRATION_MANDATE_COMPARISON_EXAMPLE,
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

_RISK_DRAWDOWN_RESPONSE_EXAMPLE = RISK_DRAWDOWN_RESPONSE_EXAMPLE

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
