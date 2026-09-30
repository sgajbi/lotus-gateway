from __future__ import annotations

from collections.abc import Mapping, Sequence

from prometheus_client import Counter, Gauge, Histogram

from app.observability.analytics_ui_fields import (
    GATEWAY_ANALYTICS_DEGRADED_REASON_ALIASES,
    GATEWAY_ANALYTICS_DEGRADED_REASON_VOCABULARY,
    validate_gateway_analytics_ui_log_fields,
)

GATEWAY_ANALYTICS_UI_METRIC_FAMILIES = (
    "lotus_gateway_analytics_fanout_duration_seconds",
    "lotus_gateway_analytics_degraded_total",
    "lotus_gateway_attribution_trend_active_windows",
    "lotus_gateway_attribution_trend_queued_windows",
    "lotus_gateway_attribution_trend_window_dispositions_total",
    "lotus_gateway_attribution_trend_request_duration_seconds",
)

GATEWAY_ANALYTICS_FANOUT_DURATION_LABELS = ("operation", "service", "status_class")
GATEWAY_ANALYTICS_DEGRADED_LABELS = ("operation", "service", "reason")
GATEWAY_ATTRIBUTION_TREND_WORK_LABELS = ("service",)
GATEWAY_ATTRIBUTION_TREND_WINDOW_DISPOSITION_LABELS = ("state",)
GATEWAY_ATTRIBUTION_TREND_REQUEST_DURATION_LABELS = ("state",)
GATEWAY_ANALYTICS_UI_METRIC_LABEL_CONTRACTS = {
    "lotus_gateway_analytics_fanout_duration_seconds": GATEWAY_ANALYTICS_FANOUT_DURATION_LABELS,
    "lotus_gateway_analytics_degraded_total": GATEWAY_ANALYTICS_DEGRADED_LABELS,
    "lotus_gateway_attribution_trend_active_windows": GATEWAY_ATTRIBUTION_TREND_WORK_LABELS,
    "lotus_gateway_attribution_trend_queued_windows": GATEWAY_ATTRIBUTION_TREND_WORK_LABELS,
    "lotus_gateway_attribution_trend_window_dispositions_total": (
        GATEWAY_ATTRIBUTION_TREND_WINDOW_DISPOSITION_LABELS
    ),
    "lotus_gateway_attribution_trend_request_duration_seconds": (
        GATEWAY_ATTRIBUTION_TREND_REQUEST_DURATION_LABELS
    ),
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

GATEWAY_ATTRIBUTION_TREND_ACTIVE_WINDOWS = Gauge(
    "lotus_gateway_attribution_trend_active_windows",
    "Attribution trend source windows currently admitted in this Gateway process.",
    GATEWAY_ATTRIBUTION_TREND_WORK_LABELS,
)
GATEWAY_ATTRIBUTION_TREND_QUEUED_WINDOWS = Gauge(
    "lotus_gateway_attribution_trend_queued_windows",
    "Attribution trend source windows waiting for this Gateway process bulkhead.",
    GATEWAY_ATTRIBUTION_TREND_WORK_LABELS,
)
GATEWAY_ATTRIBUTION_TREND_WINDOW_DISPOSITIONS_TOTAL = Counter(
    "lotus_gateway_attribution_trend_window_dispositions_total",
    "Final attribution trend window dispositions.",
    GATEWAY_ATTRIBUTION_TREND_WINDOW_DISPOSITION_LABELS,
)
GATEWAY_ATTRIBUTION_TREND_REQUEST_DURATION_SECONDS = Histogram(
    "lotus_gateway_attribution_trend_request_duration_seconds",
    "Elapsed attribution trend orchestration duration.",
    GATEWAY_ATTRIBUTION_TREND_REQUEST_DURATION_LABELS,
)


def record_attribution_trend_window_dispositions(rows: Sequence[object]) -> None:
    """Record the final parsed row state, after payload validation has completed."""
    for row in rows:
        state = getattr(row, "completion_state", "failed")
        disposition = state if state in {"completed", "failed", "timed_out"} else "failed"
        GATEWAY_ATTRIBUTION_TREND_WINDOW_DISPOSITIONS_TOTAL.labels(state=disposition).inc()


def record_attribution_trend_orchestration(
    *,
    request_state: str,
    duration_seconds: float,
) -> None:
    """Record only the bounded orchestration lifecycle; rows are recorded after parsing."""
    bounded_request_state = (
        request_state
        if request_state in {"complete", "partial", "timed_out", "cancelled"}
        else "failed"
    )
    GATEWAY_ATTRIBUTION_TREND_REQUEST_DURATION_SECONDS.labels(state=bounded_request_state).observe(
        duration_seconds
    )


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


def _bounded_gateway_analytics_degraded_reason(value: object) -> str:
    normalized = _safe_metric_dimension(str(value or "unknown"), default="unknown")
    if normalized in GATEWAY_ANALYTICS_DEGRADED_REASON_VOCABULARY:
        return normalized
    return GATEWAY_ANALYTICS_DEGRADED_REASON_ALIASES.get(normalized, "unknown")


def _safe_metric_dimension(value: str | None, *, default: str) -> str:
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
