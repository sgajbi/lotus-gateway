from collections.abc import Sequence
from decimal import Decimal, DecimalException, localcontext
from typing import Literal, Protocol

DecimalRoundingMode = Literal[
    "ROUND_CEILING",
    "ROUND_DOWN",
    "ROUND_FLOOR",
    "ROUND_HALF_DOWN",
    "ROUND_HALF_EVEN",
    "ROUND_HALF_UP",
    "ROUND_UP",
    "ROUND_05UP",
]


class AllocationContributorLike(Protocol):
    @property
    def component_weight(self) -> Decimal | None: ...

    @property
    def market_value_reporting_currency(self) -> Decimal | None: ...

    @property
    def bucket_weight(self) -> Decimal | None: ...


class AllocationBucketLike(Protocol):
    @property
    def market_value_reporting_currency(self) -> Decimal | None: ...

    @property
    def weight(self) -> Decimal | None: ...

    @property
    def position_count(self) -> int: ...

    @property
    def contributor_count(self) -> int: ...

    @property
    def contributors(self) -> Sequence[AllocationContributorLike]: ...

    @property
    def contributors_truncated(self) -> bool: ...

    @property
    def omitted_market_value_reporting_currency(self) -> Decimal | None: ...


class AllocationViewLike(Protocol):
    @property
    def total_market_value_reporting_currency(self) -> Decimal | None: ...

    @property
    def buckets(self) -> Sequence[AllocationBucketLike]: ...


class _NumericPolicyLike(Protocol):
    @property
    def precision(self) -> int: ...

    @property
    def working_precision(self) -> int: ...

    @property
    def scale(self) -> int: ...

    @property
    def rounding(self) -> str: ...


class _LineageLike(Protocol):
    @property
    def intermediate_precision(self) -> int: ...

    @property
    def numeric_output_policy(self) -> _NumericPolicyLike | None: ...


def _expected_weight(
    numerator: Decimal,
    denominator: Decimal,
    lineage: _LineageLike,
) -> Decimal:
    policy = lineage.numeric_output_policy
    with localcontext() as context:
        context.prec = policy.working_precision if policy else lineage.intermediate_precision
        try:
            ratio = numerator / denominator
            if policy:
                return ratio.quantize(
                    Decimal("1").scaleb(-policy.scale),
                    rounding=policy.rounding,
                )
            return ratio
        except (DecimalException, TypeError, ValueError) as exc:
            raise ValueError("allocation weight arithmetic policy is unusable") from exc


def _require_policy_bound(value: Decimal, policy: _NumericPolicyLike) -> None:
    if not value.is_finite():
        raise ValueError("allocation numeric output must be finite")
    if value.is_zero():
        return
    digits = list(value.as_tuple().digits)
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int):
        raise ValueError("allocation numeric output must be finite")
    while digits and digits[-1] == 0 and exponent < 0:
        digits.pop()
        exponent += 1
    fractional_digits = max(-exponent, 0)
    integer_digits = max(len(digits) + exponent, 0)
    if fractional_digits > policy.scale or integer_digits > policy.precision - policy.scale:
        raise ValueError("allocation numeric output exceeds its declared precision or scale")


def _validate_policy_bounds(
    views: Sequence[AllocationViewLike], total: Decimal | None, policy: _NumericPolicyLike
) -> None:
    values = [total]
    for view in views:
        values.append(view.total_market_value_reporting_currency)
        for bucket in view.buckets:
            values.extend(
                (
                    bucket.market_value_reporting_currency,
                    bucket.weight,
                    bucket.omitted_market_value_reporting_currency,
                )
            )
            for contributor in bucket.contributors:
                values.extend(
                    (
                        contributor.component_weight,
                        contributor.market_value_reporting_currency,
                        contributor.bucket_weight,
                    )
                )
    for value in values:
        if value is not None:
            _require_policy_bound(value, policy)


def validate_allocation_numeric_outputs(
    views: Sequence[AllocationViewLike],
    total: Decimal | None,
    lineage: _LineageLike,
) -> None:
    if lineage.numeric_output_policy:
        _validate_policy_bounds(views, total, lineage.numeric_output_policy)
    for bucket in (bucket for view in views for bucket in view.buckets):
        bucket_value = bucket.market_value_reporting_currency
        if (
            total
            and bucket_value is not None
            and bucket.weight != _expected_weight(bucket_value, total, lineage)
        ):
            raise ValueError("allocation bucket weight must reconcile to the portfolio total")
        if bucket_value:
            for contributor in bucket.contributors:
                value = contributor.market_value_reporting_currency
                if value is not None and contributor.bucket_weight != _expected_weight(
                    value, bucket_value, lineage
                ):
                    raise ValueError("contributor weight must reconcile to the bucket value")
