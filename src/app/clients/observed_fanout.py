from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.clients.http_resilience import request_binary_with_retry, request_with_retry
from app.clients.http_response_payloads import communication_failure_result
from app.observability.analytics_ui import (
    emit_gateway_analytics_fanout_log,
    gateway_analytics_fanout_timer,
)


async def request_observed_fanout(
    *,
    logger: logging.Logger,
    service: str,
    operation: str,
    method: str,
    url: str,
    timeout_seconds: float,
    max_retries: int = 2,
    backoff_seconds: float = 0.2,
    retry_status_codes: set[int] | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    retry_timeout_exceptions: bool = True,
    total_deadline_seconds: float | None = None,
) -> tuple[int, dict[str, Any]]:
    started_at = gateway_analytics_fanout_timer()
    request_kwargs: dict[str, Any] = {
        "method": method,
        "url": url,
        "timeout_seconds": timeout_seconds,
        "max_retries": max_retries,
        "backoff_seconds": backoff_seconds,
        "retry_status_codes": retry_status_codes,
        "params": params,
        "headers": headers,
        "json_body": json_body,
        "data": data,
        "files": files,
        "retry_timeout_exceptions": retry_timeout_exceptions,
    }
    try:
        if total_deadline_seconds is None:
            status_code, payload = await request_with_retry(**request_kwargs)
        else:
            async with asyncio.timeout(total_deadline_seconds):
                status_code, payload = await request_with_retry(**request_kwargs)
    except TimeoutError:
        status_code, payload = communication_failure_result("elapsed deadline exceeded")
    emit_gateway_analytics_fanout_log(
        logger=logger,
        started_at=started_at,
        service=service,
        operation=operation,
        status_code=status_code,
        payload=payload,
    )
    return status_code, payload


async def request_observed_binary_fanout(
    *,
    logger: logging.Logger,
    service: str,
    operation: str,
    method: str,
    url: str,
    timeout_seconds: float,
    max_retries: int = 2,
    backoff_seconds: float = 0.2,
    retry_status_codes: set[int] | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    retry_timeout_exceptions: bool = True,
) -> tuple[int, bytes, dict[str, str], dict[str, Any]]:
    started_at = gateway_analytics_fanout_timer()
    status_code, content, response_headers, error_payload = await request_binary_with_retry(
        method=method,
        url=url,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
        retry_status_codes=retry_status_codes,
        params=params,
        headers=headers,
        retry_timeout_exceptions=retry_timeout_exceptions,
    )
    emit_gateway_analytics_fanout_log(
        logger=logger,
        started_at=started_at,
        service=service,
        operation=operation,
        status_code=status_code,
        payload=error_payload,
    )
    return status_code, content, response_headers, error_payload
