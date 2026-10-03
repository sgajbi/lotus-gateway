from collections.abc import Sequence
from decimal import Decimal, DecimalException, localcontext
from typing import Protocol


class _NumericPolicyLike(Protocol):
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


class _ContributorLike(Protocol):
    @property
    def market_value_reporting_currency(self) -> Decimal | None: ...

    @property
    def bucket_weight(self) -> Decimal | None: ...


class _BucketLike(Protocol):
    @property
    def market_value_reporting_currency(self) -> Decimal | None: ...

    @property
    def weight(self) -> Decimal | None: ...

    @property
    def contributors(self) -> Sequence[_ContributorLike]: ...


class _ViewLike(Protocol):
    @property
    def buckets(self) -> Sequence[_BucketLike]: ...


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


def validate_allocation_weight_arithmetic(
    views: Sequence[_ViewLike],
    total: Decimal | None,
    lineage: _LineageLike,
) -> None:
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
