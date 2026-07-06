from __future__ import annotations

import logging
import os
import time
from collections.abc import Mapping
from typing import Any

from prometheus_client import Counter, Histogram

from app.observability.analytics_ui_fields import (
    ANALYTICS_UI_ALLOWED_LABELS,
    ANALYTICS_UI_ATTENTION_EVENT_ATTRIBUTES,
    ANALYTICS_UI_ATTENTION_EVENT_TYPES,
    ANALYTICS_UI_AUDIT_EVENT_ATTRIBUTES,
    ANALYTICS_UI_AUDIT_EVENT_TYPES,
    ANALYTICS_UI_FORBIDDEN_FIELDS,
    ANALYTICS_UI_SEVERITY_LEVELS,
    ANALYTICS_UI_STATE_VOCABULARY,
    ANALYTICS_UI_TRACE_ATTRIBUTES,
    GATEWAY_ANALYTICS_UI_AUDIT_LOG_EVENTS,
    GATEWAY_ANALYTICS_UI_AUDIT_LOG_FIELDS,
    GATEWAY_ANALYTICS_UI_LOG_EVENTS,
    GATEWAY_ANALYTICS_UI_STRUCTURED_LOG_FIELDS,
    is_analytics_ui_state,
    validate_analytics_ui_attributes,
    validate_analytics_ui_labels,
    validate_gateway_analytics_ui_audit_log_fields,
    validate_gateway_analytics_ui_log_fields,
)
from app.services.source_supportability import extract_calculation_supportability

__all__ = [
    "ANALYTICS_UI_ALLOWED_LABELS",
    "ANALYTICS_UI_ATTENTION_EVENT_ATTRIBUTES",
    "ANALYTICS_UI_ATTENTION_EVENT_TYPES",
    "ANALYTICS_UI_AUDIT_EVENT_ATTRIBUTES",
    "ANALYTICS_UI_AUDIT_EVENT_TYPES",
    "ANALYTICS_UI_FORBIDDEN_FIELDS",
    "ANALYTICS_UI_SEVERITY_LEVELS",
    "ANALYTICS_UI_STATE_VOCABULARY",
    "ANALYTICS_UI_TRACE_ATTRIBUTES",
    "GATEWAY_ANALYTICS_DEGRADED_LABELS",
    "GATEWAY_ANALYTICS_DEGRADED_REASON_VOCABULARY",
    "GATEWAY_ANALYTICS_DEGRADED_TOTAL",
    "GATEWAY_ANALYTICS_FANOUT_DURATION_LABELS",
    "GATEWAY_ANALYTICS_FANOUT_DURATION_SECONDS",
    "GATEWAY_ANALYTICS_UI_AUDIT_LOG_EVENTS",
    "GATEWAY_ANALYTICS_UI_AUDIT_LOG_FIELDS",
    "GATEWAY_ANALYTICS_UI_LOG_EVENTS",
    "GATEWAY_ANALYTICS_UI_METRIC_FAMILIES",
    "GATEWAY_ANALYTICS_UI_METRIC_LABEL_CONTRACTS",
    "GATEWAY_ANALYTICS_UI_STRUCTURED_LOG_FIELDS",
    "emit_gateway_analytics_fanout_log",
    "emit_gateway_analytics_read_audit_log",
    "emit_gateway_protected_diagnostics_audit_log",
    "gateway_analytics_fanout_timer",
    "is_analytics_ui_state",
    "record_gateway_analytics_fanout_metrics",
    "validate_analytics_ui_attributes",
    "validate_analytics_ui_labels",
    "validate_gateway_analytics_ui_audit_log_fields",
    "validate_gateway_analytics_ui_log_fields",
]

GATEWAY_ANALYTICS_UI_METRIC_FAMILIES = (
    "lotus_gateway_analytics_fanout_duration_seconds",
    "lotus_gateway_analytics_degraded_total",
)

GATEWAY_ANALYTICS_FANOUT_DURATION_LABELS = ("operation", "service", "status_class")
GATEWAY_ANALYTICS_DEGRADED_LABELS = ("operation", "service", "reason")
GATEWAY_ANALYTICS_DEGRADED_REASON_VOCABULARY = frozenset(
    {
        "source_supportability_partial",
        "source_supportability_degraded",
        "upstream_warning",
        "partial_failure_code",
        "upstream_unavailable",
        "upstream_error",
        "unknown",
    }
)
_GATEWAY_ANALYTICS_DEGRADED_REASON_ALIASES = {
    "upstream-unavailable": "upstream_unavailable",
    "upstream_unavailable": "upstream_unavailable",
    "upstream-error": "upstream_error",
    "upstream_error": "upstream_error",
}

GATEWAY_ANALYTICS_UI_METRIC_LABEL_CONTRACTS = {
    "lotus_gateway_analytics_fanout_duration_seconds": GATEWAY_ANALYTICS_FANOUT_DURATION_LABELS,
    "lotus_gateway_analytics_degraded_total": GATEWAY_ANALYTICS_DEGRADED_LABELS,
}

GATEWAY_ANALYTICS_FANOUT_DURATION_SECONDS = Histogram(
    "lotus_gateway_analytics_fanout_duration_seconds",
    "Duration of Gateway analytics upstream fan-out calls.",
    GATEWAY_ANALYTICS_FANOUT_DURATION_LABELS,
)

GATEWAY_ANALYTICS_DEGRADED_TOTAL = Counter(
    "lotus_gateway_analytics_degraded_total",
    "Count of degraded Gateway analytics upstream fan-out calls.",
    GATEWAY_ANALYTICS_DEGRADED_LABELS,
)


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
    record_gateway_analytics_fanout_metrics(fields)
    event = str(fields["event"])
    logger.info(event, extra={"extra_fields": fields})


def record_gateway_analytics_fanout_metrics(fields: Mapping[str, object]) -> None:
    validated_fields = validate_gateway_analytics_ui_log_fields(fields)
    operation = str(validated_fields["operation"])
    service = str(validated_fields["service"])
    status_class = str(validated_fields["status_class"])
    duration_ms = validated_fields["duration_ms"]
    if not isinstance(duration_ms, int | float):
        raise ValueError("Analytics UI fan-out duration_ms must be numeric")
    GATEWAY_ANALYTICS_FANOUT_DURATION_SECONDS.labels(
        operation=operation,
        service=service,
        status_class=status_class,
    ).observe(float(duration_ms) / 1000)

    if validated_fields.get("event") == "gateway.analytics.fanout.degraded":
        GATEWAY_ANALYTICS_DEGRADED_TOTAL.labels(
            operation=operation,
            service=service,
            reason=_bounded_gateway_analytics_degraded_reason(validated_fields.get("reason")),
        ).inc()


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


def emit_gateway_protected_diagnostics_audit_log(
    *,
    logger: logging.Logger,
    status_code: int,
    reason: str,
) -> None:
    fields = {
        "event": "gateway.analytics.audit.protected_diagnostics_lookup",
        "route": "workbench-analytics",
        "panel": "protected-diagnostics",
        "operation": "analytics-ui.protected-diagnostics.lookup",
        "state": "ready" if 0 < status_code < 400 else "permission_blocked",
        "reason": reason,
        "status_class": _status_class(status_code),
        "region": _safe_dimension(os.getenv("LOTUS_REGION"), default="unknown"),
        "environment": _safe_dimension(os.getenv("LOTUS_ENVIRONMENT"), default="local"),
    }
    logger.info(
        "gateway.analytics.audit.protected_diagnostics_lookup",
        extra={"extra_fields": validate_gateway_analytics_ui_audit_log_fields(fields)},
    )


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
    calculation_supportability = extract_calculation_supportability(payload)
    if calculation_supportability is not None:
        if calculation_supportability.state in {"ready", "supported"}:
            return "ready"
        if calculation_supportability.state in {"partial", "stale"}:
            return "partial"
        return "degraded"

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
    calculation_supportability = extract_calculation_supportability(payload)
    if calculation_supportability is not None and calculation_supportability.state not in {
        "ready",
        "supported",
    }:
        supportability_state = str(calculation_supportability.state).lower()
        if supportability_state in {"partial", "stale"}:
            return "source_supportability_partial"
        return "source_supportability_degraded"

    warnings = payload.get("warnings")
    if isinstance(warnings, list) and warnings:
        return "upstream_warning"

    partial_failures = payload.get("partial_failures")
    if isinstance(partial_failures, list):
        for failure in partial_failures:
            if isinstance(failure, Mapping):
                error_code = failure.get("error_code")
                if error_code:
                    return "partial_failure_code"

    if status_code >= 500:
        return "upstream_unavailable"
    if status_code >= 400:
        return "upstream_error"
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
    if operation.startswith("advisor_brief."):
        return "advisor-brief"
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
    previous_was_separator = False
    characters: list[str] = []
    for character in value.strip().lower():
        if character.isalnum() or character in {"_", "."}:
            characters.append(character)
            previous_was_separator = False
            continue
        if character in {"-", " ", "/"} and not previous_was_separator:
            characters.append("-")
            previous_was_separator = True
    cleaned = "".join(characters).strip("-")
    return cleaned[:64] or default


def _bounded_gateway_analytics_degraded_reason(value: object) -> str:
    normalized = _safe_dimension(str(value or "unknown"), default="unknown")
    if normalized in GATEWAY_ANALYTICS_DEGRADED_REASON_VOCABULARY:
        return normalized
    return _GATEWAY_ANALYTICS_DEGRADED_REASON_ALIASES.get(normalized, "unknown")
