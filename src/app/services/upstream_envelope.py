"""Shared service-layer helpers for upstream-backed gateway envelopes."""

from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.config import settings
from app.services.upstream_error_policy import (
    GATEWAY_SERVICE_ERROR_STATUS_RULES,
    GatewayServiceErrorStatusRule,
    ProductSafeServiceErrorConfig,
    gateway_status_for_service_error,
    safe_upstream_detail,
)

EnvelopeT = TypeVar("EnvelopeT", bound=BaseModel)
PayloadT = TypeVar("PayloadT", bound=BaseModel)
ErrorDetailT = TypeVar("ErrorDetailT", bound=BaseModel)

__all__ = [
    "GATEWAY_SERVICE_ERROR_STATUS_RULES",
    "GatewayServiceErrorStatusRule",
    "ProductSafeServiceErrorConfig",
    "build_gateway_envelope",
    "build_product_safe_upstream_status_gateway_envelope",
    "build_product_safe_upstream_status_payload_gateway_envelope",
    "build_typed_gateway_envelope",
    "build_upstream_status_gateway_envelope",
    "build_upstream_status_payload_gateway_envelope",
    "raise_configured_product_safe_service_error",
    "raise_for_upstream_error",
    "raise_gateway_mapped_service_error",
    "raise_product_safe_gateway_unavailable_error",
    "raise_product_safe_service_error",
    "raise_product_safe_upstream_error",
    "safe_upstream_detail",
]


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


def build_product_safe_upstream_status_gateway_envelope(
    response_model: type[EnvelopeT],
    *,
    correlation_id: str,
    upstream_status: int,
    upstream_payload: dict[str, Any],
    supportability: BaseModel,
    error_model: type[ErrorDetailT],
    error_code: str,
    default_detail: str,
) -> EnvelopeT:
    """Raise product-safe upstream errors, otherwise build a supportability envelope."""

    raise_product_safe_upstream_error(
        upstream_status,
        upstream_payload,
        error_model=error_model,
        error_code=error_code,
        default_detail=default_detail,
    )
    return build_upstream_status_gateway_envelope(
        response_model,
        correlation_id=correlation_id,
        upstream_status=upstream_status,
        upstream_payload=upstream_payload,
        supportability=supportability,
    )


def build_upstream_status_payload_gateway_envelope(
    response_model: type[EnvelopeT],
    *,
    correlation_id: str,
    upstream_status: int,
    upstream_payload: dict[str, Any],
) -> EnvelopeT:
    """Build a Gateway envelope that exposes upstream status and preserves payload data."""

    return response_model(
        correlation_id=correlation_id,
        contract_version=settings.contract_version,
        upstream_status=upstream_status,
        data=upstream_payload,
    )


def build_product_safe_upstream_status_payload_gateway_envelope(
    response_model: type[EnvelopeT],
    *,
    correlation_id: str,
    upstream_status: int,
    upstream_payload: dict[str, Any],
    error_model: type[ErrorDetailT],
    error_code: str,
    default_detail: str,
) -> EnvelopeT:
    """Raise product-safe upstream errors, otherwise build a payload-only envelope."""

    raise_product_safe_upstream_error(
        upstream_status,
        upstream_payload,
        error_model=error_model,
        error_code=error_code,
        default_detail=default_detail,
    )
    return build_upstream_status_payload_gateway_envelope(
        response_model,
        correlation_id=correlation_id,
        upstream_status=upstream_status,
        upstream_payload=upstream_payload,
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


def raise_product_safe_service_error(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    *,
    source_service: str,
    error_code: str,
    default_detail: str,
) -> None:
    """Raise a product-safe Gateway error for upstream services without a typed detail model."""

    if upstream_status < status.HTTP_400_BAD_REQUEST:
        return

    _raise_product_safe_service_error(
        upstream_status,
        upstream_payload,
        config=ProductSafeServiceErrorConfig(
            source_service=source_service,
            error_code=error_code,
            default_detail=default_detail,
        ),
    )


def raise_configured_product_safe_service_error(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    *,
    config: ProductSafeServiceErrorConfig,
) -> None:
    """Raise a product-safe Gateway error from a code-owned service error config."""

    if upstream_status < status.HTTP_400_BAD_REQUEST:
        return

    _raise_product_safe_service_error(
        upstream_status,
        upstream_payload,
        config=config,
    )


def _raise_product_safe_service_error(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    *,
    config: ProductSafeServiceErrorConfig,
) -> None:
    raise HTTPException(
        status_code=upstream_status,
        detail={
            "source_service": config.source_service,
            "upstream_status": upstream_status,
            "error_code": config.error_code,
            "detail": safe_upstream_detail(
                upstream_payload,
                default_detail=config.default_detail,
            ),
        },
    )


def raise_product_safe_gateway_unavailable_error(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    *,
    source_service: str,
    error_code: str,
    default_detail: str,
) -> None:
    """Raise a product-safe 502 for unavailable upstream-backed Gateway routes."""

    if upstream_status < status.HTTP_400_BAD_REQUEST:
        return

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "source_service": source_service,
            "upstream_status": upstream_status,
            "error_code": error_code,
            "detail": safe_upstream_detail(upstream_payload, default_detail=default_detail),
        },
    )


def raise_gateway_mapped_service_error(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    *,
    source_service: str,
    error_code: str = "UPSTREAM_SERVICE_ERROR",
    default_detail: str = "Upstream service request failed.",
) -> None:
    """Raise an upstream service error using Gateway's canonical status mapping."""

    if upstream_status < status.HTTP_400_BAD_REQUEST:
        return

    gateway_status = gateway_status_for_service_error(upstream_status)

    raise HTTPException(
        status_code=gateway_status,
        detail={
            "source_service": source_service,
            "upstream_status": upstream_status,
            "error_code": error_code,
            "detail": safe_upstream_detail(upstream_payload, default_detail=default_detail),
        },
    )
