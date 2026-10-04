import pytest

from app.services.source_supportability import (
    extract_calculation_supportability,
    source_supportability_reason,
)


def _history_coverage():
    return {
        "status": "partial",
        "calculation_basis": "available_window",
        "requested_start_date": "2025-01-10",
        "requested_end_date": "2026-01-09",
        "covered_start_date": "2026-01-05",
        "covered_end_date": "2026-01-09",
        "effective_start_date": "2026-01-05",
        "effective_end_date": "2026-01-09",
        "calendar_basis": "natural_days",
        "missing_required_observation_count": 360,
        "missing_required_observation_dates_sample": ["2025-01-10"],
        "reason_codes": ["leading_history_missing"],
    }


def test_source_history_is_preserved_without_reconstructing_dates():
    history = _history_coverage()
    result = extract_calculation_supportability(
        {
            "calculation_supportability": {
                "state": "degraded",
                "reason": "partial_history_coverage",
                "history_coverage": history,
            }
        }
    )
    assert result is not None
    assert result.history_coverage.model_dump(mode="json") == history


@pytest.mark.parametrize("history", [{}, [], "complete", {"status": "complete"}])
def test_present_malformed_history_reuses_invalid_source_boundary(history):
    assert (
        extract_calculation_supportability(
            {
                "calculation_supportability": {
                    "state": "ready",
                    "history_coverage": history,
                }
            }
        )
        is None
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "ready"),
        ("calculation_basis", "inferred_window"),
        ("calendar_basis", "attested_holidays"),
        ("requested_start_date", "not-a-date"),
        ("missing_required_observation_count", -1),
        ("missing_required_observation_count", True),
        ("missing_required_observation_count", "360"),
        ("reason_codes", ["private diagnostic"]),
        ("missing_required_observation_dates_sample", ["2025-01-10"] * 11),
    ],
)
def test_invalid_history_fields_are_not_coerced_to_qualified_history(field, value):
    history = _history_coverage()
    history[field] = value
    assert (
        extract_calculation_supportability(
            {
                "calculation_supportability": {
                    "state": "ready",
                    "history_coverage": history,
                }
            }
        )
        is None
    )


@pytest.mark.parametrize(
    "reason", ["leading_history_missing", "interior_history_missing", "trailing_history_missing"]
)
def test_source_gap_reason_and_missing_dates_are_not_reinterpreted(reason):
    history = _history_coverage()
    history["reason_codes"] = [reason]
    result = extract_calculation_supportability(
        {
            "calculation_supportability": {
                "state": "degraded",
                "reason": "partial_history_coverage",
                "history_coverage": history,
            }
        }
    )
    assert result is not None
    assert result.history_coverage.model_dump(mode="json") == history


def test_extract_calculation_supportability_reads_nested_metadata() -> None:
    supportability = extract_calculation_supportability(
        {
            "metadata": {
                "calculation_supportability": {
                    "state": "stale",
                    "reason": "Source data window stale",
                    "freshness_bucket": "stale",
                    "source_service": "lotus-performance",
                }
            }
        }
    )

    assert supportability is not None
    assert supportability.state == "stale"
    assert supportability.risk_contract_state == "partial"
    assert supportability.performance_evidence_state == "partial"
    assert supportability.reason == "Source data window stale"
    assert supportability.freshness_bucket == "stale"
    assert supportability.source_service == "lotus-performance"


def test_extract_calculation_supportability_reads_top_level_legacy_shape() -> None:
    supportability = extract_calculation_supportability(
        {
            "calculation_supportability": {
                "supportability_state": "complete",
                "freshness_bucket": "fresh",
            }
        }
    )

    assert supportability is not None
    assert supportability.state == "ready"
    assert supportability.risk_contract_state == "ready"
    assert supportability.performance_evidence_state == "supported"
    assert (
        source_supportability_reason(
            supportability,
            default_ready_reason="Source calculation supportability was confirmed upstream.",
        )
        == "Source calculation supportability freshness is fresh."
    )


def test_extract_calculation_supportability_rejects_unknown_state() -> None:
    assert (
        extract_calculation_supportability(
            {"metadata": {"calculation_supportability": {"state": "caller-owned"}}}
        )
        is None
    )
