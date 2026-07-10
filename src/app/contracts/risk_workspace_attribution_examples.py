from typing import Any

RISK_ATTRIBUTION_PAYLOAD_EXAMPLE: dict[str, Any] = {
    "controls": {
        "attribution_types": [
            {"key": "TOTAL_RISK", "label": "Total Risk", "state": "ready", "reason": None},
            {"key": "ACTIVE_RISK", "label": "Active Risk", "state": "ready", "reason": None},
        ],
        "grouping_dimensions": [
            {
                "key": "POSITION",
                "label": "Position",
                "state": "ready",
                "reason": None,
                "supported_attribution_types": ["TOTAL_RISK", "ACTIVE_RISK"],
            },
            {
                "key": "SECTOR",
                "label": "Sector",
                "state": "ready",
                "reason": None,
                "supported_attribution_types": ["TOTAL_RISK", "ACTIVE_RISK"],
            },
            {
                "key": "ASSET_CLASS",
                "label": "Asset Class",
                "state": "ready",
                "reason": None,
                "supported_attribution_types": ["TOTAL_RISK", "ACTIVE_RISK"],
            },
            {
                "key": "ISSUER",
                "label": "Issuer",
                "state": "blocked",
                "reason": (
                    "Benchmark issuer exposure semantics are not yet approved for active risk."
                ),
                "supported_attribution_types": ["TOTAL_RISK"],
            },
        ],
        "selected_attribution_type": "ACTIVE_RISK",
        "selected_grouping_dimension": "ASSET_CLASS",
    },
    "periods": [
        {
            "key": "YTD",
            "label": "YTD",
            "start_date": "2026-01-01",
            "end_date": "2026-04-04",
            "attribution_sets": [
                {
                    "attribution_type": "ACTIVE_RISK",
                    "metric": "TRACKING_ERROR",
                    "grouping_dimension": "ASSET_CLASS",
                    "total_value": 0.034,
                    "reconciled_sum": 0.033,
                    "residual": 0.001,
                    "contributors": [
                        {
                            "group_key": "EQUITY",
                            "group_label": "Equity",
                            "weight_average": 0.62,
                            "marginal_contribution": 0.018,
                            "component_contribution": 0.016,
                            "percent_contribution": 0.47,
                        }
                    ],
                    "quality_flags": ["covariance:benchmark_overlap_warning"],
                }
            ],
            "error": None,
        }
    ],
    "methodology_context": {
        "covariance_method": "EMPIRICAL",
        "annualization_basis": 252,
        "requested_attribution_types": ["ACTIVE_RISK"],
        "requested_metrics": ["TRACKING_ERROR"],
        "requested_grouping_dimensions": ["ASSET_CLASS"],
        "min_observations_policy": "STRICT",
        "stateful_active_risk_supported_grouping_dimensions": [
            "POSITION",
            "SECTOR",
            "ASSET_CLASS",
        ],
        "stateful_active_risk_gated_grouping_dimensions": ["ISSUER"],
        "stateful_active_risk_gate_reason": (
            "Benchmark issuer exposure semantics are not yet approved for active risk."
        ),
    },
}
