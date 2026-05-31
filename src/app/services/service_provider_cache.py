from collections.abc import Callable
from typing import TypeVar

ServiceT = TypeVar("ServiceT")


def resolve_cached_service(
    service: ServiceT | None,
    cached_signature: tuple[object, ...] | None,
    current_signature: tuple[object, ...],
    build_service: Callable[[], ServiceT],
) -> tuple[ServiceT, tuple[object, ...]]:
    if service is None or cached_signature != current_signature:
        return build_service(), current_signature
    return service, cached_signature
