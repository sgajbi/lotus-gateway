import pytest

from app.observability.analytics_ui import (
    ANALYTICS_UI_ALLOWED_LABELS,
    ANALYTICS_UI_FORBIDDEN_FIELDS,
    ANALYTICS_UI_STATE_VOCABULARY,
    GATEWAY_ANALYTICS_UI_METRIC_FAMILIES,
    is_analytics_ui_state,
    validate_analytics_ui_labels,
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


def test_validate_analytics_ui_labels_rejects_ad_hoc_label_drift() -> None:
    assert "portfolio_id" not in ANALYTICS_UI_ALLOWED_LABELS
    with pytest.raises(ValueError, match="unsupported field"):
        validate_analytics_ui_labels({"custom_dimension": "drift"})


def test_validate_analytics_ui_labels_drops_empty_optional_values() -> None:
    assert validate_analytics_ui_labels(
        {"route": "portfolio", "operation": "", "state": None, "status_class": "5xx"}
    ) == {"route": "portfolio", "status_class": "5xx"}
