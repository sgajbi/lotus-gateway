import pytest

from app.observability.analytics_ui import (
    ANALYTICS_UI_ALLOWED_LABELS,
    ANALYTICS_UI_ATTENTION_EVENT_ATTRIBUTES,
    ANALYTICS_UI_ATTENTION_EVENT_TYPES,
    ANALYTICS_UI_AUDIT_EVENT_ATTRIBUTES,
    ANALYTICS_UI_AUDIT_EVENT_TYPES,
    ANALYTICS_UI_FORBIDDEN_FIELDS,
    ANALYTICS_UI_SEVERITY_LEVELS,
    ANALYTICS_UI_STATE_VOCABULARY,
    ANALYTICS_UI_TRACE_ATTRIBUTES,
    GATEWAY_ANALYTICS_DEGRADED_TOTAL,
    GATEWAY_ANALYTICS_FANOUT_DURATION_SECONDS,
    GATEWAY_ANALYTICS_UI_AUDIT_LOG_EVENTS,
    GATEWAY_ANALYTICS_UI_AUDIT_LOG_FIELDS,
    GATEWAY_ANALYTICS_UI_LOG_EVENTS,
    GATEWAY_ANALYTICS_UI_METRIC_FAMILIES,
    GATEWAY_ANALYTICS_UI_STRUCTURED_LOG_FIELDS,
    emit_gateway_analytics_fanout_log,
    emit_gateway_protected_diagnostics_audit_log,
    is_analytics_ui_state,
    record_gateway_analytics_fanout_metrics,
    validate_analytics_ui_attributes,
    validate_analytics_ui_labels,
    validate_gateway_analytics_ui_audit_log_fields,
    validate_gateway_analytics_ui_log_fields,
)


def test_gateway_metric_families_are_explicitly_scoped_to_gateway() -> None:
    assert GATEWAY_ANALYTICS_UI_METRIC_FAMILIES == (
        "lotus_gateway_analytics_fanout_duration_seconds",
        "lotus_gateway_analytics_degraded_total",
    )
    duration_labels = GATEWAY_ANALYTICS_FANOUT_DURATION_SECONDS._labelnames
    degraded_labels = GATEWAY_ANALYTICS_DEGRADED_TOTAL._labelnames
    assert duration_labels == ("operation", "service", "status_class")
    assert degraded_labels == ("operation", "service", "reason")


def test_state_vocabulary_matches_governed_analytics_ui_states() -> None:
    assert "permission_blocked" in ANALYTICS_UI_STATE_VOCABULARY
    assert is_analytics_ui_state("degraded")
    assert not is_analytics_ui_state("blocked")


def test_gateway_log_events_and_severity_vocabularies_are_explicit() -> None:
    assert GATEWAY_ANALYTICS_UI_LOG_EVENTS == (
        "gateway.analytics.fanout.completed",
        "gateway.analytics.fanout.degraded",
    )
    assert GATEWAY_ANALYTICS_UI_AUDIT_LOG_EVENTS == (
        "gateway.analytics.audit.analytics_read_allowed",
        "gateway.analytics.audit.analytics_read_denied",
        "gateway.analytics.audit.protected_diagnostics_lookup",
    )
    assert ANALYTICS_UI_SEVERITY_LEVELS == {
        "info",
        "warning",
        "action_required",
        "critical",
    }
    assert "source_partial" in ANALYTICS_UI_ATTENTION_EVENT_TYPES
    assert "analytics_read_denied" in ANALYTICS_UI_AUDIT_EVENT_TYPES
    assert GATEWAY_ANALYTICS_UI_STRUCTURED_LOG_FIELDS == (
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
    assert GATEWAY_ANALYTICS_UI_AUDIT_LOG_FIELDS == (
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


def test_trace_attention_and_audit_attributes_are_bounded_and_product_safe() -> None:
    for attributes in (
        ANALYTICS_UI_TRACE_ATTRIBUTES,
        ANALYTICS_UI_ATTENTION_EVENT_ATTRIBUTES,
        ANALYTICS_UI_AUDIT_EVENT_ATTRIBUTES,
    ):
        assert validate_analytics_ui_attributes(attributes) == attributes
        assert "portfolio_id" not in attributes
        assert "client_name" not in attributes
        assert "screen_content" not in attributes


def test_validate_analytics_ui_labels_accepts_bounded_non_sensitive_fields() -> None:
    labels = validate_analytics_ui_labels(
        {
            "route": "performance",
            "operation": "performance-summary",
            "service": "lotus-performance",
            "status_class": "2xx",
            "state": "ready",
        }
    )

    assert labels == {
        "route": "performance",
        "operation": "performance-summary",
        "service": "lotus-performance",
        "status_class": "2xx",
        "state": "ready",
    }


def test_validate_analytics_ui_labels_rejects_forbidden_sensitive_fields() -> None:
    for field in ANALYTICS_UI_FORBIDDEN_FIELDS:
        with pytest.raises(ValueError, match="forbidden field"):
            validate_analytics_ui_labels({field: "sensitive"})
        with pytest.raises(ValueError, match="forbidden field"):
            validate_analytics_ui_attributes((field,))
        with pytest.raises(ValueError, match="forbidden field"):
            validate_gateway_analytics_ui_log_fields({field: "sensitive"})
        with pytest.raises(ValueError, match="forbidden field"):
            validate_gateway_analytics_ui_audit_log_fields({field: "sensitive"})


def test_validate_analytics_ui_labels_rejects_ad_hoc_label_drift() -> None:
    assert "portfolio_id" not in ANALYTICS_UI_ALLOWED_LABELS
    with pytest.raises(ValueError, match="unsupported field"):
        validate_analytics_ui_labels({"custom_dimension": "drift"})
    with pytest.raises(ValueError, match="unsupported field"):
        validate_analytics_ui_attributes(("custom_dimension",))


def test_validate_analytics_ui_labels_drops_empty_optional_values() -> None:
    assert validate_analytics_ui_labels(
        {"route": "portfolio", "operation": "", "state": None, "status_class": "5xx"}
    ) == {"route": "portfolio", "status_class": "5xx"}


def test_validate_gateway_analytics_ui_log_fields_accepts_structured_runtime_fields() -> None:
    fields = validate_gateway_analytics_ui_log_fields(
        {
            "event": "gateway.analytics.fanout.degraded",
            "route": "workbench-analytics",
            "service": "lotus-risk",
            "operation": "analytics.risk.calculate",
            "state": "partial",
            "reason": "RISK_SUMMARY_PARTIAL",
            "supportability_state": "partial",
            "status_class": "2xx",
            "error_category": None,
            "duration_ms": 12.4,
            "warning_count": 1,
            "partial_failure_count": 1,
        }
    )

    assert fields["duration_ms"] == 12.4
    assert fields["warning_count"] == 1
    assert "error_category" not in fields


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("event", "gateway.analytics.custom", "unsupported event"),
        ("state", "blocked", "unsupported state"),
        ("status_class", "200", "unsupported status_class"),
    ],
)
def test_validate_gateway_analytics_ui_log_fields_rejects_value_drift(
    field: str,
    value: str,
    match: str,
) -> None:
    fields = {
        "event": "gateway.analytics.fanout.degraded",
        "route": "workbench-analytics",
        "service": "lotus-risk",
        "operation": "analytics.risk.calculate",
        "state": "degraded",
        "reason": "UPSTREAM_UNAVAILABLE",
        "status_class": "5xx",
        "duration_ms": 125.0,
    }
    fields[field] = value

    with pytest.raises(ValueError, match=match):
        validate_gateway_analytics_ui_log_fields(fields)


def test_validate_gateway_analytics_ui_log_fields_rejects_audit_event_drift() -> None:
    with pytest.raises(ValueError, match="unsupported event"):
        validate_gateway_analytics_ui_log_fields(
            {
                "event": "gateway.analytics.audit.analytics_read_allowed",
                "route": "workbench-analytics",
                "service": "lotus-performance",
                "operation": "performance.workspace-summary",
                "state": "ready",
                "status_class": "2xx",
                "duration_ms": 12.0,
            }
        )


def test_validate_gateway_analytics_ui_audit_log_fields_accepts_bounded_runtime_fields() -> None:
    fields = validate_gateway_analytics_ui_audit_log_fields(
        {
            "event": "gateway.analytics.audit.analytics_read_denied",
            "route": "workbench-analytics",
            "panel": "risk-summary",
            "operation": "analytics.risk.calculate",
            "state": "permission_blocked",
            "reason": "upstream_authorization_denied",
            "status_class": "4xx",
            "region": "ap-southeast-1",
            "environment": "local",
        }
    )

    assert fields["event"] == "gateway.analytics.audit.analytics_read_denied"
    assert fields["state"] == "permission_blocked"
    assert "portfolio_id" not in fields
    assert "raw_entitlement_failure" not in fields


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("event", "gateway.analytics.audit.custom", "unsupported event"),
        ("state", "denied", "unsupported state"),
        ("status_class", "403", "unsupported status_class"),
    ],
)
def test_validate_gateway_analytics_ui_audit_log_fields_rejects_value_drift(
    field: str,
    value: str,
    match: str,
) -> None:
    fields = {
        "event": "gateway.analytics.audit.analytics_read_denied",
        "route": "workbench-analytics",
        "panel": "risk-summary",
        "operation": "analytics.risk.calculate",
        "state": "permission_blocked",
        "reason": "upstream_authorization_denied",
        "status_class": "4xx",
        "region": "ap-southeast-1",
        "environment": "local",
    }
    fields[field] = value

    with pytest.raises(ValueError, match=match):
        validate_gateway_analytics_ui_audit_log_fields(fields)


def test_validate_gateway_analytics_ui_audit_log_fields_rejects_fanout_event_drift() -> None:
    with pytest.raises(ValueError, match="unsupported event"):
        validate_gateway_analytics_ui_audit_log_fields(
            {
                "event": "gateway.analytics.fanout.completed",
                "route": "workbench-analytics",
                "panel": "performance-summary",
                "operation": "performance.workspace-summary",
                "state": "ready",
                "reason": "upstream_read_succeeded",
                "status_class": "2xx",
                "region": "ap-southeast-1",
                "environment": "local",
            }
        )


def test_protected_diagnostics_audit_log_uses_bounded_fields(caplog) -> None:
    import logging

    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    logger = logging.getLogger("analytics_ui.gateway")

    emit_gateway_protected_diagnostics_audit_log(
        logger=logger,
        status_code=200,
        reason="lookup_succeeded",
    )

    record = next(
        record
        for record in caplog.records
        if record.name == "analytics_ui.gateway"
        and record.message == "gateway.analytics.audit.protected_diagnostics_lookup"
    )
    fields = record.extra_fields
    assert fields == {
        "event": "gateway.analytics.audit.protected_diagnostics_lookup",
        "route": "workbench-analytics",
        "panel": "protected-diagnostics",
        "operation": "analytics-ui.protected-diagnostics.lookup",
        "state": "ready",
        "reason": "lookup_succeeded",
        "status_class": "2xx",
        "region": "unknown",
        "environment": "local",
    }
    assert "support_reference" not in fields
    assert "trace_id" not in fields


def test_record_gateway_analytics_fanout_metrics_records_safe_labels() -> None:
    before_duration_count = _sample_value(
        GATEWAY_ANALYTICS_FANOUT_DURATION_SECONDS,
        "lotus_gateway_analytics_fanout_duration_seconds_count",
        {
            "operation": "analytics.risk.calculate",
            "service": "lotus-risk",
            "status_class": "5xx",
        },
    )
    before_degraded_count = _sample_value(
        GATEWAY_ANALYTICS_DEGRADED_TOTAL,
        "lotus_gateway_analytics_degraded_total",
        {
            "operation": "analytics.risk.calculate",
            "service": "lotus-risk",
            "reason": "upstream_unavailable",
        },
    )

    record_gateway_analytics_fanout_metrics(
        {
            "event": "gateway.analytics.fanout.degraded",
            "route": "workbench-analytics",
            "service": "lotus-risk",
            "operation": "analytics.risk.calculate",
            "state": "degraded",
            "reason": "UPSTREAM_UNAVAILABLE",
            "status_class": "5xx",
            "duration_ms": 125.0,
            "warning_count": 0,
            "partial_failure_count": 0,
        }
    )

    assert (
        _sample_value(
            GATEWAY_ANALYTICS_FANOUT_DURATION_SECONDS,
            "lotus_gateway_analytics_fanout_duration_seconds_count",
            {
                "operation": "analytics.risk.calculate",
                "service": "lotus-risk",
                "status_class": "5xx",
            },
        )
        == before_duration_count + 1
    )
    assert (
        _sample_value(
            GATEWAY_ANALYTICS_DEGRADED_TOTAL,
            "lotus_gateway_analytics_degraded_total",
            {
                "operation": "analytics.risk.calculate",
                "service": "lotus-risk",
                "reason": "upstream_unavailable",
            },
        )
        == before_degraded_count + 1
    )


def test_gateway_fanout_logs_use_source_calculation_supportability(caplog) -> None:
    import logging

    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    logger = logging.getLogger("analytics_ui.gateway")
    before_degraded_count = _sample_value(
        GATEWAY_ANALYTICS_DEGRADED_TOTAL,
        "lotus_gateway_analytics_degraded_total",
        {
            "operation": "performance.workspace-summary",
            "service": "lotus-performance",
            "reason": "source-data-window-stale",
        },
    )

    emit_gateway_analytics_fanout_log(
        logger=logger,
        started_at=0.0,
        service="lotus-performance",
        operation="performance.workspace-summary",
        status_code=200,
        payload={
            "metadata": {
                "calculation_supportability": {
                    "state": "stale",
                    "reason": "Source data window stale",
                    "freshness_bucket": "stale",
                    "source_service": "lotus-performance",
                }
            }
        },
    )

    record = next(
        record
        for record in caplog.records
        if record.name == "analytics_ui.gateway"
        and record.message == "gateway.analytics.fanout.degraded"
    )
    assert record.extra_fields["state"] == "partial"
    assert record.extra_fields["supportability_state"] == "partial"
    assert record.extra_fields["reason"] == "Source data window stale"
    assert "portfolio_id" not in record.extra_fields

    assert (
        _sample_value(
            GATEWAY_ANALYTICS_DEGRADED_TOTAL,
            "lotus_gateway_analytics_degraded_total",
            {
                "operation": "performance.workspace-summary",
                "service": "lotus-performance",
                "reason": "source-data-window-stale",
            },
        )
        == before_degraded_count + 1
    )


def test_record_gateway_analytics_fanout_metrics_rejects_sensitive_labels() -> None:
    with pytest.raises(ValueError, match="forbidden field"):
        record_gateway_analytics_fanout_metrics(
            {
                "event": "gateway.analytics.fanout.degraded",
                "route": "workbench-analytics",
                "service": "lotus-risk",
                "operation": "analytics.risk.calculate",
                "state": "degraded",
                "reason": "UPSTREAM_UNAVAILABLE",
                "status_class": "5xx",
                "duration_ms": 125.0,
                "warning_count": 0,
                "partial_failure_count": 0,
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            }
        )


def _sample_value(collector: object, sample_name: str, labels: dict[str, str]) -> float:
    for metric in collector.collect():
        for sample in metric.samples:
            if sample.name == sample_name and dict(sample.labels) == labels:
                return float(sample.value)
    return 0.0
