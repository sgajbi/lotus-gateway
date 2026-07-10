from __future__ import annotations

from collections.abc import Mapping

from prometheus_client import Counter, Histogram

from app.observability.analytics_ui_fields import (
    GATEWAY_ANALYTICS_DEGRADED_REASON_ALIASES,
    GATEWAY_ANALYTICS_DEGRADED_REASON_VOCABULARY,
    validate_gateway_analytics_ui_log_fields,
)

GATEWAY_ANALYTICS_UI_METRIC_FAMILIES = (
    "lotus_gateway_analytics_fanout_duration_seconds",
    "lotus_gateway_analytics_degraded_total",
)

GATEWAY_ANALYTICS_FANOUT_DURATION_LABELS = ("operation", "service", "status_class")
GATEWAY_ANALYTICS_DEGRADED_LABELS = ("operation", "service", "reason")
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
