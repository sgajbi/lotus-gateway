"""Core-only signed transport, redirect refusal and total logical deadline."""

import asyncio
from functools import partial
from typing import Any, Awaitable, Callable
from urllib.parse import urlsplit

import httpx

from app.clients.http_response_payloads import communication_failure_result
from app.core_execution_authority import CoreExecutionAuthority

CORE_EXECUTION_DEADLINE_SECONDS = 290.0


def _valid_core_execution_target(url: str) -> bool:
    """Validate the actual target before HTTPX can derive URL authentication."""
    try:
        target = httpx.URL(url)
        return (
            target.scheme in {"http", "https"}
            and bool(target.host)
            and (target.port is None or 0 <= target.port <= 65535)
            and not target.userinfo
            and "@" not in urlsplit(url).netloc
            and not any(ord(char) <= 32 or ord(char) == 127 for char in url)
        )
    except (httpx.InvalidURL, ValueError):
        return False


async def request_core_with_execution_authority(
    *,
    authority: CoreExecutionAuthority | None,
    headers: dict[str, str] | None,
    send: Callable[..., Awaitable[tuple[int, dict[str, Any]]]],
    **request_kwargs: Any,
) -> tuple[int, dict[str, Any]]:
    """Bound the entire enabled Core call, including signing, attempts and backoff."""
    if authority is None:
        return await send(headers=headers, **request_kwargs)
    # The observed layer must emit only the final Core outcome, after this
    # request-local execution has bounded retries and refused redirects.
    return await send(
        headers=headers,
        core_execution=partial(_execute_core_with_authority, authority=authority),
        **request_kwargs,
    )


async def _execute_core_with_authority(
    *,
    authority: CoreExecutionAuthority,
    request_kwargs: dict[str, Any],
    send: Callable[..., Awaitable[tuple[int, dict[str, Any]]]],
) -> tuple[int, dict[str, Any]]:
    try:
        async with asyncio.timeout(CORE_EXECUTION_DEADLINE_SECONDS):
            if not _valid_core_execution_target(request_kwargs["url"]):
                return communication_failure_result("core execution target refused")
            signed_headers = authority.sign(request_kwargs.get("headers") or {})
            status_code, payload = await send(
                request_kwargs={
                    **request_kwargs,
                    "headers": signed_headers,
                    "follow_redirects": False,
                }
            )
            if 300 <= status_code < 400:
                return communication_failure_result("core upstream redirect refused")
            return status_code, payload
    except TimeoutError:
        return communication_failure_result("core execution deadline exceeded")
