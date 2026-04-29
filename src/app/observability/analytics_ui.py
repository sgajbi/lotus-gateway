from __future__ import annotations

from collections.abc import Mapping

ANALYTICS_UI_ALLOWED_LABELS = frozenset(
    {
        "route",
        "panel",
        "service",
        "operation",
        "state",
        "reason",
        "freshness_bucket",
        "supportability_state",
        "attention_type",
        "severity",
        "status_class",
        "error_category",
        "region",
        "environment",
    }
)

ANALYTICS_UI_FORBIDDEN_FIELDS = frozenset(
    {
        "portfolio_id",
        "client_id",
        "client_name",
        "household_id",
        "account_id",
        "instrument_id",
        "holding_id",
        "transaction_id",
        "trace_id",
        "correlation_id",
        "document_id",
        "advisor_id",
        "advisor_behavior",
        "screen_content",
        "request_body",
        "response_body",
        "raw_entitlement_failure",
    }
)

ANALYTICS_UI_STATE_VOCABULARY = frozenset(
    {
        "loading",
        "ready",
        "empty",
        "partial",
        "stale",
        "degraded",
        "error",
        "permission_blocked",
        "unsupported",
    }
)

GATEWAY_ANALYTICS_UI_METRIC_FAMILIES = (
    "lotus_gateway_analytics_fanout_duration_seconds",
    "lotus_gateway_analytics_degraded_total",
)


def is_analytics_ui_state(value: str) -> bool:
    return value in ANALYTICS_UI_STATE_VOCABULARY


def validate_analytics_ui_labels(labels: Mapping[str, object]) -> dict[str, str]:
    label_names = set(labels)
    forbidden = sorted(label_names & ANALYTICS_UI_FORBIDDEN_FIELDS)
    if forbidden:
        raise ValueError(f"Analytics UI labels include forbidden field(s): {', '.join(forbidden)}")

    unsupported = sorted(label_names - ANALYTICS_UI_ALLOWED_LABELS)
    if unsupported:
        raise ValueError(
            f"Analytics UI labels include unsupported field(s): {', '.join(unsupported)}"
        )

    return {
        key: str(value) for key, value in labels.items() if value is not None and str(value) != ""
    }
