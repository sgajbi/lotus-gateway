from collections.abc import Sequence
from decimal import Decimal
from typing import Protocol

ZERO = Decimal("0")


class _ContributorLike(Protocol):
    @property
    def market_value_reporting_currency(self) -> Decimal | None: ...

    @property
    def bucket_weight(self) -> Decimal | None: ...


class _BucketLike(Protocol):
    @property
    def market_value_reporting_currency(self) -> Decimal | None: ...

    @property
    def position_count(self) -> int: ...

    @property
    def contributor_count(self) -> int: ...

    @property
    def contributors(self) -> Sequence[_ContributorLike]: ...

    @property
    def contributors_truncated(self) -> bool: ...

    @property
    def omitted_market_value_reporting_currency(self) -> Decimal | None: ...


def _validate_count_shape(bucket: _BucketLike) -> None:
    retained_count = len(bucket.contributors)
    if retained_count > bucket.contributor_count:
        raise ValueError("contributors cannot exceed contributor_count")
    if bucket.contributor_count > bucket.position_count:
        raise ValueError("contributor_count cannot exceed position_count")
    if bucket.contributors_truncated != (retained_count < bucket.contributor_count):
        raise ValueError("contributors_truncated must match omitted contributor rows")


def _validate_null_qualification(bucket: _BucketLike) -> None:
    bucket_value_known = bucket.market_value_reporting_currency is not None
    residual_known = bucket.omitted_market_value_reporting_currency is not None
    if bucket_value_known != residual_known:
        raise ValueError("bucket value and omitted residual must share null qualification")
    denominator_known = (
        bucket.market_value_reporting_currency is not None
        and bucket.market_value_reporting_currency != ZERO
    )
    if any(
        (contributor.bucket_weight is not None) != denominator_known
        for contributor in bucket.contributors
    ):
        raise ValueError("contributor weights require a known nonzero bucket denominator")


def _validate_value_reconciliation(bucket: _BucketLike) -> None:
    bucket_value = bucket.market_value_reporting_currency
    omitted_residual = bucket.omitted_market_value_reporting_currency
    if bucket_value is None or omitted_residual is None:
        return
    retained_values = [item.market_value_reporting_currency for item in bucket.contributors]
    if any(value is None for value in retained_values):
        raise ValueError("known bucket value cannot contain unknown contributor value")
    retained_value = sum((value for value in retained_values if value is not None), ZERO)
    if retained_value + omitted_residual != bucket_value:
        raise ValueError("contributors and omitted residual must reconcile to bucket value")
    if not bucket.contributors_truncated and omitted_residual != ZERO:
        raise ValueError("untruncated contributors require a zero omitted residual")


def validate_allocation_bucket(bucket: _BucketLike) -> None:
    _validate_count_shape(bucket)
    _validate_null_qualification(bucket)
    _validate_value_reconciliation(bucket)
