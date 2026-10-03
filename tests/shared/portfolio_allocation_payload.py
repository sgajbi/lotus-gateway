from typing import Any

ALLOCATION_VIEW_DIMENSIONS = ("asset_class", "currency", "sector", "region")


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


def allocation_source_evidence(
    *,
    portfolio_id: str = "PF_1001",
    resolved_as_of_date: str = "2026-03-27",
    reporting_currency: str = "USD",
    **evidence_kwargs: Any,
) -> dict[str, Any]:
    return {
        "scope_type": "portfolio",
        "scope": {"portfolio_id": portfolio_id},
        "resolved_as_of_date": resolved_as_of_date,
        "reporting_currency": reporting_currency,
        **allocation_evidence(**evidence_kwargs),
    }


def complete_allocation_views(primary_view: dict[str, Any]) -> list[dict[str, Any]]:
    """Return one source view for every dimension requested by Gateway."""

    primary_dimension = primary_view["dimension"]
    total = primary_view["total_market_value_reporting_currency"]
    return [
        primary_view
        if dimension == primary_dimension
        else {
            "dimension": dimension,
            "total_market_value_reporting_currency": total,
            "buckets": [],
        }
        for dimension in ALLOCATION_VIEW_DIMENSIONS
    ]


def empty_allocation_views(
    total_market_value_reporting_currency: str | int | float | None,
) -> list[dict[str, Any]]:
    """Return an empty source view for every dimension requested by Gateway."""

    return [
        {
            "dimension": dimension,
            "total_market_value_reporting_currency": total_market_value_reporting_currency,
            "buckets": [],
        }
        for dimension in ALLOCATION_VIEW_DIMENSIONS
    ]
