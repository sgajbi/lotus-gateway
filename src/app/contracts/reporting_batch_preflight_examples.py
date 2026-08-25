from typing import Any

REPORT_BATCH_PREFLIGHT_RESPONSE_EXAMPLE: dict[str, Any] = {
    "contract_version": "report-batch-preflight.v1",
    "source_authority": "lotus-core",
    "request": {
        "selector_mode": "explicit_portfolio_list",
        "portfolio_ids": ["PB_SG_GLOBAL_BAL_001", "PB_SG_PRIVATE_002"],
        "as_of_date": "2026-04-22",
        "requested_output_formats": ["pdf"],
        "reporting_currency": "USD",
        "options": {"sections": ["OVERVIEW", "PERFORMANCE"]},
        "max_batch_size": 250,
    },
    "state": "partial",
    "reason_code": "candidate_scope_partial",
    "message": "Some requested portfolios are not currently ready for reporting.",
    "source_posture": {
        "state": "ready",
        "reason_code": "membership_source_ready",
        "message": "Core membership evidence is current for the requested business date.",
        "as_of_date": "2026-04-22",
    },
    "configuration_posture": {
        "state": "ready",
        "reason_code": "report_configuration_ready",
        "message": "The requested report configuration is source-backed.",
    },
    "candidate_count": 2,
    "ready_count": 1,
    "partial_count": 0,
    "stale_count": 0,
    "permission_blocked_count": 1,
    "unavailable_count": 0,
    "candidates": [
        {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "state": "ready",
            "reason_code": "portfolio_reporting_ready",
            "message": "The portfolio is active in the authenticated source-owned book.",
            "source_evidence": {
                "source_system": "lotus-core",
                "source_contract_version": "PortfolioManagerBookMembership:v1",
                "as_of_date": "2026-04-22",
                "membership_reference": "membership-001",
            },
        },
        {
            "portfolio_id": "PB_SG_PRIVATE_002",
            "state": "permission_blocked",
            "reason_code": "portfolio_not_entitled",
            "message": "The portfolio is not available in the authenticated book.",
            "source_evidence": None,
        },
    ],
    "correlation_id": "corr-report-batch-preflight",
}


__all__ = ["REPORT_BATCH_PREFLIGHT_RESPONSE_EXAMPLE"]
