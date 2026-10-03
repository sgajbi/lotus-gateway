from typing import Any


def allocation_evidence(
    *,
    total_market_value_reporting_currency: str | int | float | None = "1000.00",
    coverage_state: str = "COMPLETE",
    coverage_reason: str = "all_source_positions_covered",
    snapshot_row_count: int = 1,
    expected_open_position_count: int = 1,
    valued_position_count: int = 1,
    unvalued_position_count: int = 0,
) -> dict[str, Any]:
    """Return independently specified Core-compatible allocation evidence for tests."""

    return {
        "total_market_value_reporting_currency": total_market_value_reporting_currency,
        "valuation_coverage": {
            "coverage_state": coverage_state,
            "coverage_reason": coverage_reason,
            "snapshot_row_count": snapshot_row_count,
            "expected_open_position_count": expected_open_position_count,
            "valued_position_count": valued_position_count,
            "unvalued_position_count": unvalued_position_count,
        },
        "calculation_lineage": {
            "algorithm_id": "PORTFOLIO_ALLOCATION",
            "algorithm_version": 1,
            "intermediate_precision": 28,
            "input_content_hash": "a" * 64,
            "calculation_content_hash": "b" * 64,
            "output_content_hash": "c" * 64,
            "numeric_output_policy": None,
        },
    }
