"""Shared service-layer helpers for upstream-backed gateway envelopes."""

from typing import Any, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.config import settings

EnvelopeT = TypeVar("EnvelopeT", bound=BaseModel)
PayloadT = TypeVar("PayloadT", bound=BaseModel)
ErrorDetailT = TypeVar("ErrorDetailT", bound=BaseModel)


def build_gateway_envelope(
    response_model: type[EnvelopeT],
    *,
    correlation_id: str,
    upstream_payload: dict[str, Any],
) -> EnvelopeT:
    """Build the standard Gateway response envelope without rewriting upstream truth."""

    return response_model(
        correlation_id=correlation_id,
        contract_version=settings.contract_version,
        data=upstream_payload,
    )


def build_typed_gateway_envelope(
    response_model: type[EnvelopeT],
    payload_model: type[PayloadT],
    *,
    correlation_id: str,
    upstream_payload: dict[str, Any],
) -> EnvelopeT:
    """Build a Gateway envelope after validating a typed upstream payload projection."""

    return response_model(
        correlation_id=correlation_id,
        contract_version=settings.contract_version,
        data=payload_model.model_validate(upstream_payload),
    )


def build_upstream_status_gateway_envelope(
    response_model: type[EnvelopeT],
    *,
    correlation_id: str,
    upstream_status: int,
    upstream_payload: dict[str, Any],
    supportability: BaseModel,
) -> EnvelopeT:
    """Build a Gateway envelope that exposes upstream status and derived supportability."""

    return response_model(
        correlation_id=correlation_id,
        contract_version=settings.contract_version,
        upstream_status=upstream_status,
        supportability=supportability,
        data=upstream_payload,
    )


def raise_for_upstream_error(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    *,
    stringify_payload: bool = False,
) -> None:
    """Raise a Gateway HTTP error while preserving the service's existing error contract."""

    if upstream_status < status.HTTP_400_BAD_REQUEST:
        return

    detail: str | dict[str, Any] = upstream_payload
    if stringify_payload and not isinstance(detail, str):
        detail = str(detail)
    raise HTTPException(status_code=upstream_status, detail=detail)


def safe_upstream_detail(payload: dict[str, Any], *, default_detail: str) -> str:
    """Extract a bounded product-safe error summary from an upstream error payload."""

    detail = payload.get("detail") or payload.get("message") or payload.get("error")
    if isinstance(detail, str):
        return detail
    if detail is not None:
        return str(detail)
    return default_detail


def raise_product_safe_upstream_error(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    *,
    error_model: type[ErrorDetailT],
    error_code: str,
    default_detail: str,
) -> None:
    """Raise a typed product-safe Gateway error for upstream-backed route families."""

    if upstream_status < status.HTTP_400_BAD_REQUEST:
        return

    raise HTTPException(
        status_code=upstream_status,
        detail=error_model(
            upstream_status=upstream_status,
            error_code=error_code,
            detail=safe_upstream_detail(upstream_payload, default_detail=default_detail),
        ).model_dump(),
    )
