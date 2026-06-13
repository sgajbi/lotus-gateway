from typing import Any

from fastapi import HTTPException, status

from app.contracts.portfolio import PortfolioPartialFailure
from app.services.portfolio_workspace_payloads import optional_text
from app.services.upstream_envelope import safe_upstream_detail

UpstreamResult = tuple[int, dict[str, Any]]


def require_payload(
    result: UpstreamResult,
    unavailable_detail_prefix: str,
) -> dict[str, Any]:
    status_code, payload = result
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=build_safe_upstream_error_detail(
                unavailable_detail_prefix,
                payload,
            ),
        )
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{unavailable_detail_prefix}: invalid payload",
        )
    return payload


def raise_on_upstream_client_error(
    result: UpstreamResult,
    *,
    detail_prefix: str,
) -> None:
    status_code, payload = result
    if status.HTTP_400_BAD_REQUEST <= status_code < status.HTTP_500_INTERNAL_SERVER_ERROR:
        raise HTTPException(
            status_code=status_code,
            detail=build_safe_upstream_error_detail(detail_prefix, payload),
        )


def build_safe_upstream_error_detail(
    detail_prefix: str,
    payload: dict[str, Any],
) -> str:
    detail = safe_upstream_detail(payload, default_detail="upstream request failed")
    return f"{detail_prefix}: {detail}"


def optional_payload(
    result: UpstreamResult,
    source_service: str,
    warning_code: str,
    warnings: list[str],
    partial_failures: list[PortfolioPartialFailure],
) -> dict[str, Any] | None:
    status_code, payload = result
    if status_code < status.HTTP_400_BAD_REQUEST and isinstance(payload, dict):
        return payload
    warnings.append(warning_code)
    partial_failures.append(
        PortfolioPartialFailure(
            source_service=source_service,
            error_code=warning_code,
            detail=format_upstream_error_detail(payload),
        )
    )
    return None


def format_upstream_error_detail(payload: Any) -> str:
    if isinstance(payload, dict):
        detail = optional_text(payload.get("detail"))
        if detail is not None:
            return detail
    return str(payload)
