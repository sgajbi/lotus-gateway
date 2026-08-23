"""Shared typed error construction for upstream-backed Gateway envelopes."""

from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.services.upstream_error_policy import safe_upstream_detail

ErrorDetailT = TypeVar("ErrorDetailT", bound=BaseModel)


def raise_product_safe_upstream_error(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    *,
    error_model: type[ErrorDetailT],
    error_code: str,
    default_detail: str,
    detail_fields: Mapping[str, Any] | None = None,
    detail_resolver: Callable[[int, dict[str, Any], str], str] | None = None,
) -> None:
    """Raise a typed product-safe error with optional bounded fields and detail policy."""

    if upstream_status < status.HTTP_400_BAD_REQUEST:
        return

    detail = safe_upstream_detail(upstream_payload, default_detail=default_detail)
    if detail_resolver is not None:
        detail = detail_resolver(upstream_status, upstream_payload, detail)
    error_detail: dict[str, Any] = {
        "upstream_status": upstream_status,
        "error_code": error_code,
        "detail": detail,
    }
    if detail_fields is not None:
        error_detail.update(detail_fields)

    raise HTTPException(
        status_code=upstream_status,
        detail=error_model(**error_detail).model_dump(),
    )
