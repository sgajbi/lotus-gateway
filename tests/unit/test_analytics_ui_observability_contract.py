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
    GATEWAY_ANALYTICS_UI_LOG_EVENTS,
    GATEWAY_ANALYTICS_UI_METRIC_FAMILIES,
    GATEWAY_ANALYTICS_UI_STRUCTURED_LOG_FIELDS,
    is_analytics_ui_state,
    validate_analytics_ui_attributes,
    validate_analytics_ui_labels,
    validate_gateway_analytics_ui_log_fields,
)


def test_gateway_metric_families_are_explicitly_scoped_to_gateway() -> None:
    assert GATEWAY_ANALYTICS_UI_METRIC_FAMILIES == (
        "lotus_gateway_analytics_fanout_duration_seconds",
        "lotus_gateway_analytics_degraded_total",
    )


def test_state_vocabulary_matches_governed_analytics_ui_states() -> None:
    assert "permission_blocked" in ANALYTICS_UI_STATE_VOCABULARY
    assert is_analytics_ui_state("degraded")
    assert not is_analytics_ui_state("blocked")


def test_gateway_log_events_and_severity_vocabularies_are_explicit() -> None:
    assert GATEWAY_ANALYTICS_UI_LOG_EVENTS == (
        "gateway.analytics.fanout.completed",
        "gateway.analytics.fanout.degraded",
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
