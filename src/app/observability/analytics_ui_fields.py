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
        "session_id",
        "simulation_session_id",
        "upload_id",
        "trace_id",
        "correlation_id",
        "document_id",
        "advisor_id",
        "advisor_behavior",
        "screen_content",
        "request_body",
        "response_body",
        "raw_prompt",
        "model_output",
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

GATEWAY_ANALYTICS_UI_LOG_EVENTS = (
    "gateway.analytics.fanout.completed",
    "gateway.analytics.fanout.degraded",
)

GATEWAY_ANALYTICS_UI_AUDIT_LOG_EVENTS = (
    "gateway.analytics.audit.analytics_read_allowed",
    "gateway.analytics.audit.analytics_read_denied",
    "gateway.analytics.audit.protected_diagnostics_lookup",
)

GATEWAY_ANALYTICS_UI_STRUCTURED_LOG_FIELDS = (
    "event",
    "route",
    "service",
    "operation",
    "state",
    "reason",
    "freshness_bucket",
    "supportability_state",
    "status_class",
    "error_category",
    "duration_ms",
    "warning_count",
    "partial_failure_count",
)

GATEWAY_ANALYTICS_UI_AUDIT_LOG_FIELDS = (
    "event",
    "route",
    "panel",
    "operation",
    "state",
    "reason",
    "status_class",
    "region",
    "environment",
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


def validate_gateway_analytics_ui_log_fields(fields: Mapping[str, object]) -> dict[str, object]:
    return _validate_gateway_analytics_ui_fields(
        fields=fields,
        supported_fields=set(GATEWAY_ANALYTICS_UI_STRUCTURED_LOG_FIELDS),
        supported_events=set(GATEWAY_ANALYTICS_UI_LOG_EVENTS),
        error_prefix="Analytics UI log fields",
    )


def validate_gateway_analytics_ui_audit_log_fields(
    fields: Mapping[str, object],
) -> dict[str, object]:
    return _validate_gateway_analytics_ui_fields(
        fields=fields,
        supported_fields=set(GATEWAY_ANALYTICS_UI_AUDIT_LOG_FIELDS),
        supported_events=set(GATEWAY_ANALYTICS_UI_AUDIT_LOG_EVENTS),
        error_prefix="Analytics UI audit log fields",
    )


def _validate_gateway_analytics_ui_fields(
    *,
    fields: Mapping[str, object],
    supported_fields: set[str],
    supported_events: set[str],
    error_prefix: str,
) -> dict[str, object]:
    field_names = set(fields)
    forbidden = sorted(field_names & ANALYTICS_UI_FORBIDDEN_FIELDS)
    if forbidden:
        raise ValueError(f"{error_prefix} include forbidden field(s): {', '.join(forbidden)}")

    unsupported = sorted(field_names - supported_fields)
    if unsupported:
        raise ValueError(f"{error_prefix} include unsupported field(s): {', '.join(unsupported)}")

    _validate_gateway_analytics_ui_field_values(
        fields=fields,
        supported_events=supported_events,
        error_prefix=error_prefix,
    )
    return {key: value for key, value in fields.items() if value is not None and value != ""}


def _validate_gateway_analytics_ui_field_values(
    *,
    fields: Mapping[str, object],
    supported_events: set[str],
    error_prefix: str,
) -> None:
    event = fields.get("event")
    if event is not None and event not in supported_events:
        raise ValueError(f"{error_prefix} include unsupported event: {event}")

    state = fields.get("state")
    if state is not None and not is_analytics_ui_state(str(state)):
        raise ValueError(f"{error_prefix} include unsupported state: {state}")

    status_class = fields.get("status_class")
    if status_class is not None and str(status_class) not in {
        "1xx",
        "2xx",
        "3xx",
        "4xx",
        "5xx",
        "unknown",
    }:
        raise ValueError(f"{error_prefix} include unsupported status_class: {status_class}")
