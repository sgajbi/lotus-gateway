"""Product-safe upstream error policy shared by Gateway envelope helpers."""

import re
from dataclasses import dataclass

from fastapi import status


@dataclass(frozen=True)
class GatewayServiceErrorStatusRule:
    upstream_statuses: frozenset[int]
    gateway_status: int

    def matches(self, upstream_status: int) -> bool:
        return upstream_status in self.upstream_statuses


GATEWAY_SERVICE_ERROR_STATUS_RULES = (
    GatewayServiceErrorStatusRule(
        upstream_statuses=frozenset({status.HTTP_404_NOT_FOUND}),
        gateway_status=status.HTTP_404_NOT_FOUND,
    ),
    GatewayServiceErrorStatusRule(
        upstream_statuses=frozenset(
            {
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            }
        ),
        gateway_status=status.HTTP_400_BAD_REQUEST,
    ),
)

_CODE_LIKE_UPSTREAM_DETAIL = re.compile(r"^[A-Za-z][A-Za-z0-9_.:]{0,95}$")
_SENSITIVE_UPSTREAM_DETAIL_TOKENS = (
    "account",
    "client",
    "correlation",
    "document",
    "entitlement",
    "portfolio",
    "prompt",
    "request",
    "response",
    "session",
    "trace",
)


@dataclass(frozen=True)
class ProductSafeServiceErrorConfig:
    source_service: str
    error_code: str
    default_detail: str


def safe_upstream_detail(payload: dict[str, object], *, default_detail: str) -> str:
    """Extract a bounded product-safe error summary from an upstream error payload."""

    detail = payload.get("detail") or payload.get("message") or payload.get("error")
    if isinstance(detail, dict):
        code = detail.get("code")
        if safe_code := _safe_upstream_machine_detail(code):
            return safe_code
        reason = detail.get("reason")
        if safe_reason := _safe_upstream_machine_detail(reason):
            return safe_reason
        message = detail.get("message")
        if safe_message := _safe_upstream_machine_detail(message):
            return safe_message
        return default_detail
    if isinstance(detail, str):
        return _safe_upstream_machine_detail(detail) or default_detail
    return default_detail


def _safe_upstream_machine_detail(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or not _CODE_LIKE_UPSTREAM_DETAIL.fullmatch(stripped):
        return None
    normalized = stripped.lower()
    if any(token in normalized for token in _SENSITIVE_UPSTREAM_DETAIL_TOKENS):
        return None
    if "pb_" in normalized or "traceback" in normalized or "://" in normalized:
        return None
    return stripped


def gateway_status_for_service_error(upstream_status: int) -> int:
    for rule in GATEWAY_SERVICE_ERROR_STATUS_RULES:
        if rule.matches(upstream_status):
            return rule.gateway_status
    return status.HTTP_502_BAD_GATEWAY
