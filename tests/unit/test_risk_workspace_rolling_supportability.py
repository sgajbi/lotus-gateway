from app.contracts.risk_workspace import WorkbenchRiskSupportabilityItem
from app.services.risk_workspace_rolling_supportability import (
    rolling_supportability_from_payload,
)
from app.services.risk_workspace_source_supportability import (
    append_source_calculation_supportability,
)


def test_rolling_supportability_preserves_first_paint_and_sharpe_posture() -> None:
    supportability = rolling_supportability_from_payload(
        results={"YTD": {"window_results": []}},
        benchmark_code=None,
        include_time_series=False,
        sharpe_fallback_reason="Risk-free series unavailable.",
        upstream_payload={},
    )

    by_key = {item.key: item for item in supportability}
    assert by_key["portfolio_returns"].state == "ready"
    assert by_key["benchmark_returns"].state == "partial"
    assert by_key["risk_free_series"].state == "partial"
    assert by_key["risk_free_series"].reason == "Risk-free series unavailable."
    assert by_key["rolling_time_series"].state == "partial"
    assert "first paint" in (by_key["rolling_time_series"].reason or "")


def test_append_source_calculation_supportability_preserves_upstream_posture() -> None:
    supportability = [
        WorkbenchRiskSupportabilityItem(
            key="portfolio_returns",
            label="Portfolio returns",
            state="ready",
            source_service="lotus-risk",
        )
    ]

    append_source_calculation_supportability(
        supportability=supportability,
        upstream_payload={
            "metadata": {
                "calculation_supportability": {
                    "state": "stale",
                    "reason": "Risk source data window stale.",
                    "freshness_bucket": "stale",
                    "source_service": "lotus-risk",
                }
            }
        },
    )

    source_supportability = supportability[-1]
    assert source_supportability.key == "source_calculation"
    assert source_supportability.state == "partial"
    assert source_supportability.reason == "Risk source data window stale."
    assert source_supportability.source_service == "lotus-risk"
