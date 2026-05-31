"""Shared service-layer helpers for upstream-backed gateway envelopes."""

from typing import Any, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.config import settings

EnvelopeT = TypeVar("EnvelopeT", bound=BaseModel)


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
