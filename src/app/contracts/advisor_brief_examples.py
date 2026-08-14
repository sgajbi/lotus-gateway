from __future__ import annotations

from typing import Any

ADVISOR_BRIEF_RESPONSE_EXAMPLE: dict[str, Any] = {
    "correlation_id": "corr-advisor-brief-1",
    "contract_version": "v1",
    "portfolio_id": "PF_1001",
    "portfolio": {
        "portfolio_id": "PF_1001",
        "client_id": "CIF_1001",
        "base_currency": "USD",
        "booking_center_code": "SG",
    },
    "as_of_date": "2026-04-04",
    "period": "YTD",
    "report_start_date": "2026-01-01",
    "report_end_date": "2026-04-04",
    "detail_basis": "NET",
    "chart_frequency": "monthly",
    "contribution_dimension": "asset_class",
    "attribution_dimension": "asset_class",
    "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
    "status": "partial",
    "summary": (
        "YTD portfolio return for PF 1001 is 1.25% versus Private Banking "
        "Global Balanced 60/40 7.93%, with active return -6.68%."
    ),
    "talking_points": [
        {
            "headline": "Portfolio return is 1.25% versus benchmark 7.93%.",
            "detail": "Active return is -6.68% for the selected YTD period.",
            "tone": "warning",
            "evidence_refs": [
                {
                    "metric_label": "Active Return",
                    "metric_value": "-6.68%",
                    "source_surface": "performance.return_path",
                    "target_mode": "summary",
                    "route": (
                        "/performance?portfolioId=PF_1001&period=YTD"
                        "&detailBasis=NET&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
                    ),
                }
            ],
        }
    ],
    "recommended_actions": [
        {
            "label": "Open Return Path",
            "target_mode": "summary",
            "route": (
                "/performance?portfolioId=PF_1001&period=YTD"
                "&detailBasis=NET&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
            ),
        }
    ],
    "risks_and_exceptions": [
        {
            "headline": "Attribution is unavailable.",
            "detail": "Attribution detail is not available for the current selection.",
            "tone": "warning",
            "evidence_refs": [
                {
                    "metric_label": "Attribution",
                    "metric_value": "Unavailable",
                    "source_surface": "performance.attribution",
                    "target_mode": "analysis",
                    "route": (
                        "/performance?portfolioId=PF_1001&period=YTD"
                        "&detailBasis=NET&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
                    ),
                }
            ],
        }
    ],
    "source_metrics": [
        {
            "label": "Portfolio Return",
            "value": "1.25%",
            "support_label": "YTD NET",
            "target_mode": "summary",
            "route": (
                "/performance?portfolioId=PF_1001&period=YTD"
                "&detailBasis=NET&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
            ),
            "state": "ready",
        },
        {
            "label": "Active Return",
            "value": "-6.68%",
            "support_label": "2026-01-01 to 2026-04-04",
            "target_mode": "summary",
            "route": (
                "/performance?portfolioId=PF_1001&period=YTD"
                "&detailBasis=NET&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
            ),
            "state": "partial",
        },
    ],
    "supportability": [
        {
            "label": "Portfolio",
            "value": "Ready",
            "tone": "success",
            "reason": None,
        },
        {
            "label": "Attribution",
            "value": "Unavailable",
            "tone": "danger",
            "reason": "Attribution detail is not available for the current selection.",
        },
        {
            "label": "Advisor Brief",
            "value": "Partial",
            "tone": "warn",
            "reason": None,
        },
    ],
    "ai_audit": {
        "task_id": "explain.v1",
        "output_label": "EXPLANATION_ONLY",
        "provider_mode": "local_openai_compatible",
        "provider_id": "text.local",
        "adapter_kind": "OPENAI_COMPATIBLE_LOCAL",
        "model_id": "qwen3:8b",
        "generated_at": "2026-04-04T07:45:21Z",
        "stubbed": False,
        "source_refs": [
            "lotus-gateway:workbench:PF_1001:performance-summary:YTD",
            "lotus-gateway:workbench:PF_1001:performance-details:YTD",
        ],
    },
    "ai_evidence": {
        "descriptors": [
            {
                "evidence_type": "source_fact_bundle",
                "summary": "Grounded in gateway performance workspace facts.",
                "attributes": {"portfolio_id": "PF_1001", "period": "YTD"},
            }
        ]
    },
    "workflow_pack_run": {
        "run_id": "packrun_advisor_brief_air_123",
        "runtime_state": "COMPLETED",
        "review_state": "AWAITING_REVIEW",
        "latest_review_event_at": None,
        "latest_review_actor": None,
        "review_transition_count": 0,
        "has_review_history": False,
        "allowed_review_actions": [
            "ACCEPT",
            "REJECT",
            "REVISE",
            "SUPERSEDE",
            "ABANDON",
        ],
        "supportability_status": "ACTION_REQUIRED",
        "review_pending": True,
        "superseded": False,
        "workflow_authority_owner": "lotus-gateway",
        "current_summary_note": (
            "Run completed but still requires bounded human review before downstream use."
        ),
        "replacement_run_id": None,
        "findings": [
            {
                "finding_id": "review_pending",
                "severity": "ACTION_REQUIRED",
                "summary": "Run is awaiting review.",
            }
        ],
    },
    "workflow_pack_task_flow": {
        "task_flow_id": "taskflow_advisor_brief_packrun_advisor_brief_air_123",
        "workflow_pack_id": "advisor_brief.pack",
        "version": "v1",
        "flow_status": "WAITING_FOR_REVIEW",
        "current_step_id": "generate_advisor_brief",
        "run_refs": ["packrun_advisor_brief_air_123"],
        "review_states": {"packrun_advisor_brief_air_123": "AWAITING_REVIEW"},
        "supportability_status": "ACTION_REQUIRED",
        "replacement_lineage": [],
        "handoff_refs": [],
        "updated_at": "2026-04-04T07:45:21Z",
    },
    "warnings": ["AI_DEGRADED"],
    "partial_failures": [
        {
            "source": "lotus-performance",
            "reason": "UPSTREAM_TIMEOUT",
            "detail": "Attribution detail did not complete before the gateway timeout.",
        }
    ],
}
