from collections.abc import Sequence
from decimal import Decimal

from app.services.portfolio_allocation_weight_validation import (
    AllocationBucketLike,
    AllocationViewLike,
)

TRUSTED_COVERAGE_STATES = frozenset({"COMPLETE", "MEASURED_ZERO", "CARRY_FORWARD", "LOADED_EMPTY"})
DEGRADED_COVERAGE_STATES = frozenset({"PARTIAL", "UNAVAILABLE"})
ZERO = Decimal("0")


def _validate_bucket_presence(
    views: Sequence[AllocationViewLike],
    buckets: list[AllocationBucketLike],
    coverage_state: str,
    snapshot_row_count: int,
) -> None:
    if snapshot_row_count and any(not view.buckets for view in views):
        raise ValueError("observed allocation coverage requires buckets in every view")
    if coverage_state in {"LOADED_EMPTY", "UNAVAILABLE"} and buckets:
        raise ValueError("empty allocation coverage cannot contain buckets")


def _validate_bucket_qualification(
    buckets: list[AllocationBucketLike],
    coverage_state: str,
    total_market_value_reporting_currency: Decimal | None,
) -> None:
    if coverage_state in DEGRADED_COVERAGE_STATES and any(
        bucket.weight is not None for bucket in buckets
    ):
        raise ValueError("degraded allocation valuation coverage requires unknown weights")
    if coverage_state in {"COMPLETE", "MEASURED_ZERO", "CARRY_FORWARD"} and any(
        bucket.market_value_reporting_currency is None for bucket in buckets
    ):
        raise ValueError("trusted allocation valuation coverage requires known bucket values")
    trusted_weight_denominator_known = (
        coverage_state in {"COMPLETE", "MEASURED_ZERO", "CARRY_FORWARD"}
        and total_market_value_reporting_currency is not None
        and total_market_value_reporting_currency != ZERO
    )
    if coverage_state in TRUSTED_COVERAGE_STATES and any(
        (bucket.weight is not None) != trusted_weight_denominator_known for bucket in buckets
    ):
        raise ValueError(
            "trusted allocation bucket weights require a known nonzero portfolio denominator"
        )


def _validate_measured_zero(
    buckets: list[AllocationBucketLike], coverage_state: str
) -> None:
    if coverage_state == "MEASURED_ZERO" and any(
        value != ZERO
        for bucket in buckets
        for value in (
            bucket.market_value_reporting_currency,
            bucket.omitted_market_value_reporting_currency,
            *(item.market_value_reporting_currency for item in bucket.contributors),
        )
    ):
        raise ValueError("measured-zero allocation requires zero monetary outputs")


def validate_coverage_view_content(
    views: Sequence[AllocationViewLike],
    coverage_state: str,
    total_market_value_reporting_currency: Decimal | None,
    snapshot_row_count: int,
) -> None:
    buckets = [bucket for view in views for bucket in view.buckets]
    _validate_bucket_presence(views, buckets, coverage_state, snapshot_row_count)
    _validate_bucket_qualification(buckets, coverage_state, total_market_value_reporting_currency)
    _validate_measured_zero(buckets, coverage_state)
