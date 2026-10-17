"""Core-only signed transport, redirect refusal and total logical deadline."""

import asyncio
from functools import partial
from typing import Any, Awaitable, Callable

from app.clients.http_response_payloads import communication_failure_result
from app.core_execution_authority import CoreExecutionAuthority

CORE_EXECUTION_DEADLINE_SECONDS = 290.0


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
