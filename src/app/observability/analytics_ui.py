from __future__ import annotations

from collections.abc import Iterable, Mapping

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

ANALYTICS_UI_SEVERITY_LEVELS = frozenset({"info", "warning", "action_required", "critical"})

ANALYTICS_UI_ATTENTION_EVENT_TYPES = frozenset(
    {
        "panel_stale",
        "panel_degraded",
        "panel_repeated_failure",
        "source_partial",
        "permission_blocked",
    }
)

ANALYTICS_UI_AUDIT_EVENT_TYPES = frozenset(
    {
        "analytics_read_allowed",
        "analytics_read_denied",
        "protected_diagnostics_lookup",
    }
)

GATEWAY_ANALYTICS_UI_METRIC_FAMILIES = (
    "lotus_gateway_analytics_fanout_duration_seconds",
    "lotus_gateway_analytics_degraded_total",
)

GATEWAY_ANALYTICS_UI_LOG_EVENTS = (
    "gateway.analytics.fanout.completed",
    "gateway.analytics.fanout.degraded",
)

ANALYTICS_UI_TRACE_ATTRIBUTES = (
    "route",
    "panel",
    "service",
    "operation",
    "state",
    "freshness_bucket",
    "supportability_state",
    "status_class",
    "error_category",
)

ANALYTICS_UI_ATTENTION_EVENT_ATTRIBUTES = (
    "route",
    "panel",
    "attention_type",
    "severity",
    "state",
    "reason",
    "freshness_bucket",
    "supportability_state",
)

ANALYTICS_UI_AUDIT_EVENT_ATTRIBUTES = (
    "route",
    "panel",
    "operation",
    "state",
    "reason",
    "status_class",
    "region",
    "environment",
)


def is_analytics_ui_state(value: str) -> bool:
    return value in ANALYTICS_UI_STATE_VOCABULARY


def validate_analytics_ui_labels(labels: Mapping[str, object]) -> dict[str, str]:
    validate_analytics_ui_attributes(labels)

    return {
        key: str(value) for key, value in labels.items() if value is not None and str(value) != ""
    }


def validate_analytics_ui_attributes(attribute_names: Iterable[str]) -> tuple[str, ...]:
    attribute_set = set(attribute_names)
    forbidden = sorted(attribute_set & ANALYTICS_UI_FORBIDDEN_FIELDS)
    if forbidden:
        raise ValueError(
            f"Analytics UI attributes include forbidden field(s): {', '.join(forbidden)}"
        )

    unsupported = sorted(attribute_set - ANALYTICS_UI_ALLOWED_LABELS)
    if unsupported:
        raise ValueError(
            f"Analytics UI attributes include unsupported field(s): {', '.join(unsupported)}"
        )

    return tuple(attribute_names)
