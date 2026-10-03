from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Literal, Protocol

ZERO = Decimal("0")
ONE = Decimal("1")


class _ContributorLike(Protocol):
    @property
    def contributor_type(self) -> Literal["direct_position", "look_through_component"]: ...

    @property
    def portfolio_id(self) -> str: ...

    @property
    def security_id(self) -> str: ...

    @property
    def booked_security_id(self) -> str: ...

    @property
    def source_snapshot_id(self) -> int: ...

    @property
    def component_record_id(self) -> int | None: ...

    @property
    def component_weight(self) -> Decimal | None: ...

    @property
    def component_effective_from(self) -> date | None: ...

    @property
    def component_effective_to(self) -> date | None: ...

    @property
    def component_source_system(self) -> str | None: ...

    @property
    def component_source_record_id(self) -> str | None: ...


class _BucketLike(Protocol):
    @property
    def contributors(self) -> Sequence[_ContributorLike]: ...


class _ViewLike(Protocol):
    @property
    def buckets(self) -> Sequence[_BucketLike]: ...


class _LookThroughLike(Protocol):
    @property
    def applied_mode(self) -> str: ...

    @property
    def decomposed_position_count(self) -> int: ...


def validate_allocation_contributor_identity(contributor: _ContributorLike) -> None:
    if any(
        not value.strip()
        for value in (
            contributor.portfolio_id,
            contributor.security_id,
            contributor.booked_security_id,
        )
    ):
        raise ValueError("allocation contributor identity fields must be nonblank")
    if contributor.source_snapshot_id < 1:
        raise ValueError("allocation contributor source_snapshot_id must be positive")
    component_identity = (
        contributor.component_record_id,
        contributor.component_weight,
        contributor.component_effective_from,
        contributor.component_effective_to,
        contributor.component_source_system,
        contributor.component_source_record_id,
    )
    if contributor.contributor_type == "direct_position":
        if contributor.security_id != contributor.booked_security_id or any(
            value is not None for value in component_identity
        ):
            raise ValueError("direct allocation contributor cannot carry component identity")
        return
    if contributor.component_record_id is None or contributor.component_record_id < 1:
        raise ValueError("look-through contributor requires a positive component_record_id")
    weight = contributor.component_weight
    if weight is None or not weight.is_finite() or not ZERO <= weight <= ONE:
        raise ValueError(
            "look-through contributor requires a component_weight between zero and one"
        )
    effective_from = contributor.component_effective_from
    if effective_from is None:
        raise ValueError("look-through contributor requires component_effective_from")
    if contributor.component_effective_to and contributor.component_effective_to < effective_from:
        raise ValueError("look-through contributor effective interval is invalid")


def validate_look_through_content(
    views: Sequence[_ViewLike], look_through: _LookThroughLike | None
) -> None:
    if look_through is None or look_through.applied_mode != "direct_only":
        return
    has_decomposition = look_through.decomposed_position_count or any(
        contributor.contributor_type == "look_through_component"
        for view in views
        for bucket in view.buckets
        for contributor in bucket.contributors
    )
    if has_decomposition:
        raise ValueError("direct-only allocation cannot contain look-through decomposition")
