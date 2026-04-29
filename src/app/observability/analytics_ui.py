from __future__ import annotations

import logging
import os
import time
from collections.abc import Iterable, Mapping
from typing import Any

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

GATEWAY_ANALYTICS_UI_AUDIT_LOG_EVENTS = (
    "gateway.analytics.audit.analytics_read_allowed",
    "gateway.analytics.audit.analytics_read_denied",
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
        error_prefix="Analytics UI log fields",
    )


def validate_gateway_analytics_ui_audit_log_fields(
    fields: Mapping[str, object],
) -> dict[str, object]:
    return _validate_gateway_analytics_ui_fields(
        fields=fields,
        supported_fields=set(GATEWAY_ANALYTICS_UI_AUDIT_LOG_FIELDS),
        error_prefix="Analytics UI audit log fields",
    )


def _validate_gateway_analytics_ui_fields(
    *,
    fields: Mapping[str, object],
    supported_fields: set[str],
    error_prefix: str,
) -> dict[str, object]:
    field_names = set(fields)
    forbidden = sorted(field_names & ANALYTICS_UI_FORBIDDEN_FIELDS)
    if forbidden:
        raise ValueError(
            f"{error_prefix} include forbidden field(s): {', '.join(forbidden)}"
        )

    unsupported = sorted(field_names - supported_fields)
    if unsupported:
        raise ValueError(
            f"{error_prefix} include unsupported field(s): {', '.join(unsupported)}"
        )

    return {key: value for key, value in fields.items() if value is not None and value != ""}


def gateway_analytics_fanout_timer() -> float:
    return time.perf_counter()


def emit_gateway_analytics_fanout_log(
    *,
    logger: logging.Logger,
    started_at: float,
    service: str,
    operation: str,
    status_code: int,
    payload: Mapping[str, Any],
) -> None:
    fields = _gateway_analytics_fanout_fields(
        started_at=started_at,
        service=service,
        operation=operation,
        status_code=status_code,
        payload=payload,
    )
    event = str(fields["event"])
    logger.info(event, extra={"extra_fields": fields})


def emit_gateway_analytics_read_audit_log(
    *,
    logger: logging.Logger,
    operation: str,
    status_code: int,
) -> None:
    fields = _gateway_analytics_read_audit_fields(
        operation=operation,
        status_code=status_code,
    )
    if not fields:
        return
    logger.info(str(fields["event"]), extra={"extra_fields": fields})


def _gateway_analytics_fanout_fields(
    *,
    started_at: float,
    service: str,
    operation: str,
    status_code: int,
    payload: Mapping[str, Any],
) -> dict[str, object]:
    state = _resolve_gateway_analytics_state(status_code=status_code, payload=payload)
    supportability_state = _resolve_supportability_state(payload)
    reason = _resolve_gateway_analytics_reason(status_code=status_code, payload=payload)
    fields = {
        "event": (
            "gateway.analytics.fanout.degraded"
            if state in {"partial", "degraded", "error", "unavailable"}
            else "gateway.analytics.fanout.completed"
        ),
        "route": "workbench-analytics",
        "service": service,
        "operation": operation,
        "state": "degraded" if state == "unavailable" else state,
        "reason": reason,
        "supportability_state": supportability_state,
        "status_class": _status_class(status_code),
        "error_category": _error_category(status_code),
        "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
        "warning_count": _list_count(payload.get("warnings")),
        "partial_failure_count": _list_count(payload.get("partial_failures")),
    }
    return validate_gateway_analytics_ui_log_fields(fields)


def _gateway_analytics_read_audit_fields(
    *,
    operation: str,
    status_code: int,
) -> dict[str, object] | None:
    if status_code in {401, 403}:
        event = "gateway.analytics.audit.analytics_read_denied"
        state = "permission_blocked"
        reason = "upstream_authorization_denied"
    elif 0 < status_code < 400:
        event = "gateway.analytics.audit.analytics_read_allowed"
        state = "ready"
        reason = "upstream_read_succeeded"
    else:
        return None

    fields = {
        "event": event,
        "route": "workbench-analytics",
        "panel": _panel_for_operation(operation),
        "operation": operation,
        "state": state,
        "reason": reason,
        "status_class": _status_class(status_code),
        "region": _safe_dimension(os.getenv("LOTUS_REGION"), default="unknown"),
        "environment": _safe_dimension(os.getenv("LOTUS_ENVIRONMENT"), default="local"),
    }
    return validate_gateway_analytics_ui_audit_log_fields(fields)


def _resolve_gateway_analytics_state(*, status_code: int, payload: Mapping[str, Any]) -> str:
    payload_state = payload.get("state")
    if isinstance(payload_state, str):
        normalized = _normalize_state(payload_state)
        if normalized:
            return normalized

    supportability_state = _resolve_supportability_state(payload)
    if supportability_state in {"partial", "degraded", "error", "unavailable"}:
        return supportability_state

    if _list_count(payload.get("partial_failures")):
        return "partial"
    if status_code >= 500:
        return "degraded"
    if status_code >= 400:
        return "error"
    return "ready"


def _resolve_supportability_state(payload: Mapping[str, Any]) -> str | None:
    supportability = payload.get("supportability")
    if isinstance(supportability, list):
        states = {
            normalized
            for item in supportability
            if isinstance(item, Mapping)
            for normalized in [_normalize_state(item.get("state"))]
            if normalized
        }
        if states & {"unavailable", "degraded", "error"}:
            return "degraded"
        if "partial" in states:
            return "partial"
        if "ready" in states:
            return "ready"
    return None


def _resolve_gateway_analytics_reason(
    *, status_code: int, payload: Mapping[str, Any]
) -> str | None:
    warnings = payload.get("warnings")
    if isinstance(warnings, list) and warnings:
        return str(warnings[0])

    partial_failures = payload.get("partial_failures")
    if isinstance(partial_failures, list):
        for failure in partial_failures:
            if isinstance(failure, Mapping):
                error_code = failure.get("error_code")
                if error_code:
                    return str(error_code)

    if status_code >= 500:
        return "UPSTREAM_UNAVAILABLE"
    if status_code >= 400:
        return "UPSTREAM_ERROR"
    return None


def _normalize_state(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.lower()
    if normalized == "supported":
        return "ready"
    if normalized == "blocked":
        return "permission_blocked"
    if normalized == "unavailable":
        return "unavailable"
    if normalized in ANALYTICS_UI_STATE_VOCABULARY:
        return normalized
    return None


def _status_class(status_code: int) -> str:
    if status_code <= 0:
        return "unknown"
    return f"{status_code // 100}xx"


def _error_category(status_code: int) -> str | None:
    if status_code >= 500:
        return "upstream_unavailable"
    if status_code >= 400:
        return "upstream_error"
    return None


def _list_count(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def _panel_for_operation(operation: str) -> str:
    if operation.startswith("analytics.risk."):
        return "risk-summary"
    if "workspace-summary" in operation:
        return "performance-summary"
    if operation.startswith("performance."):
        return "performance-details"
    return "unknown"


def _safe_dimension(value: str | None, *, default: str) -> str:
    if not value:
        return default
    cleaned = "".join(
        character
        for character in value.strip().lower()
        if character.isalnum() or character in {"-", "_", "."}
    )
    return cleaned[:64] or default
