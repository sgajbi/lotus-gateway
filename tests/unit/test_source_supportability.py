from app.services.source_supportability import (
    extract_calculation_supportability,
    source_supportability_reason,
)


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
