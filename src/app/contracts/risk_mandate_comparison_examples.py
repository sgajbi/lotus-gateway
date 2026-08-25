from typing import Any

MANDATE_COMPARISON_COMMON: dict[str, Any] = {
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

SUMMARY_MANDATE_COMPARISON_EXAMPLE: dict[str, Any] = {
    **MANDATE_COMPARISON_COMMON,
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

CONCENTRATION_MANDATE_COMPARISON_EXAMPLE: dict[str, Any] = {
    **MANDATE_COMPARISON_COMMON,
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
