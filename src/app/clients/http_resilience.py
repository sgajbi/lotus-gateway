import asyncio
from typing import Any

import httpx

from app.clients.http_response_payloads import (
    binary_communication_failure_result,
    communication_failure_result,
    response_payload,
    unsupported_method_payload,
)
from app.clients.http_retry_policy import (
    retry_attempts,
    retry_delay,
    should_retry_request_error,
    should_retry_status,
)

_BINARY_REQUEST_METHODS = frozenset({"GET", "POST"})
_JSON_REQUEST_METHODS = frozenset({"GET", "POST", "PUT"})


async def _send_json_request(
    *,
    client: httpx.AsyncClient,
    request_method: str,
    url: str,
    params: dict[str, Any] | None,
    headers: dict[str, str] | None,
    json_body: dict[str, Any] | None,
    data: dict[str, Any] | None,
    files: dict[str, Any] | None,
) -> httpx.Response:
    if request_method == "GET":
        return await client.get(url, params=params, headers=headers)
    if request_method == "PUT":
        return await client.put(url, headers=headers, json=json_body)
    return await client.post(
        url,
        params=params,
        headers=headers,
        json=json_body,
        data=data,
        files=files,
    )


async def _send_json_request_once(
    *,
    request_method: str,
    url: str,
    timeout_seconds: float,
    params: dict[str, Any] | None,
    headers: dict[str, str] | None,
    json_body: dict[str, Any] | None,
    data: dict[str, Any] | None,
    files: dict[str, Any] | None,
) -> httpx.Response:
    async with httpx.AsyncClient(
        timeout=timeout_seconds,
        follow_redirects=True,
    ) as client:
        return await _send_json_request(
            client=client,
            request_method=request_method,
            url=url,
            params=params,
            headers=headers,
            json_body=json_body,
            data=data,
            files=files,
        )


async def _send_binary_request_once(
    *,
    request_method: str,
    url: str,
    timeout_seconds: float,
    params: dict[str, Any] | None,
    headers: dict[str, str] | None,
) -> httpx.Response:
    async with httpx.AsyncClient(
        timeout=timeout_seconds,
        follow_redirects=True,
    ) as client:
        if request_method == "GET":
            return await client.get(url, params=params, headers=headers)
        return await client.post(url, headers=headers)


async def _sleep_before_retry(backoff_seconds: float, attempt: int) -> None:
    await asyncio.sleep(retry_delay(backoff_seconds, attempt))


async def _retry_or_return_json_response(
    *,
    response: httpx.Response,
    retry_status_codes: set[int] | None,
    attempt: int,
    max_retries: int,
    backoff_seconds: Any,
) -> tuple[int, dict[str, Any]] | None:
    if should_retry_status(
        response_status_code=response.status_code,
        retry_status_codes=retry_status_codes,
        attempt=attempt,
        max_retries=max_retries,
    ):
        await _sleep_before_retry(backoff_seconds, attempt)
        return None
    return response.status_code, response_payload(response)


async def _retry_or_return_request_error(
    *,
    exc: httpx.RequestError,
    retry_timeout_exceptions: bool,
    attempt: int,
    max_retries: int,
    backoff_seconds: Any,
) -> tuple[int, dict[str, str]] | None:
    if not should_retry_request_error(
        exc=exc,
        retry_timeout_exceptions=retry_timeout_exceptions,
        attempt=attempt,
        max_retries=max_retries,
    ):
        return communication_failure_result(exc.__class__.__name__)
    await _sleep_before_retry(backoff_seconds, attempt)
    return None


async def _send_json_retry_attempt(
    *,
    request_kwargs: dict[str, Any],
    retry_status_codes: set[int] | None,
    retry_timeout_exceptions: bool,
    attempt: int,
    max_retries: int,
    backoff_seconds: Any,
) -> tuple[int, dict[str, Any]] | None:
    try:
        response = await _send_json_request_once(**request_kwargs)
        return await _retry_or_return_json_response(
            response=response,
            retry_status_codes=retry_status_codes,
            attempt=attempt,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )
    except httpx.RequestError as exc:
        return await _retry_or_return_request_error(
            exc=exc,
            retry_timeout_exceptions=retry_timeout_exceptions,
            attempt=attempt,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )


async def _retry_or_return_binary_response(
    *,
    response: httpx.Response,
    retry_status_codes: set[int] | None,
    attempt: int,
    max_retries: int,
    backoff_seconds: Any,
) -> tuple[int, bytes, dict[str, str], dict[str, Any]] | None:
    if should_retry_status(
        response_status_code=response.status_code,
        retry_status_codes=retry_status_codes,
        attempt=attempt,
        max_retries=max_retries,
    ):
        await _sleep_before_retry(backoff_seconds, attempt)
        return None
    error_payload: dict[str, Any] = {}
    if response.status_code >= 400:
        error_payload = response_payload(response)
    return response.status_code, response.content, dict(response.headers), error_payload


async def _retry_or_return_binary_request_error(
    *,
    exc: httpx.RequestError,
    retry_timeout_exceptions: bool,
    attempt: int,
    max_retries: int,
    backoff_seconds: Any,
) -> tuple[int, bytes, dict[str, str], dict[str, str]] | None:
    if not should_retry_request_error(
        exc=exc,
        retry_timeout_exceptions=retry_timeout_exceptions,
        attempt=attempt,
        max_retries=max_retries,
    ):
        return binary_communication_failure_result(exc.__class__.__name__)
    await _sleep_before_retry(backoff_seconds, attempt)
    return None


async def _send_binary_retry_attempt(
    *,
    request_kwargs: dict[str, Any],
    retry_status_codes: set[int] | None,
    retry_timeout_exceptions: bool,
    attempt: int,
    max_retries: int,
    backoff_seconds: Any,
) -> tuple[int, bytes, dict[str, str], dict[str, Any]] | None:
    try:
        response = await _send_binary_request_once(**request_kwargs)
        return await _retry_or_return_binary_response(
            response=response,
            retry_status_codes=retry_status_codes,
            attempt=attempt,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )
    except httpx.RequestError as exc:
        return await _retry_or_return_binary_request_error(
            exc=exc,
            retry_timeout_exceptions=retry_timeout_exceptions,
            attempt=attempt,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )


async def request_with_retry(
    *,
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
) -> tuple[int, dict[str, Any]]:
    request_method = method.upper()
    if request_method not in _JSON_REQUEST_METHODS:
        return 503, unsupported_method_payload(method)

    request_kwargs = {
        "request_method": request_method,
        "url": url,
        "timeout_seconds": timeout_seconds,
        "params": params,
        "headers": headers,
        "json_body": json_body,
        "data": data,
        "files": files,
    }
    attempts = retry_attempts(max_retries)
    for attempt in range(attempts):
        result = await _send_json_retry_attempt(
            request_kwargs=request_kwargs,
            retry_status_codes=retry_status_codes,
            retry_timeout_exceptions=retry_timeout_exceptions,
            attempt=attempt,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )
        if result is not None:
            return result

    return communication_failure_result("exhausted retries")


async def request_binary_with_retry(
    *,
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
    request_method = method.upper()
    if request_method not in _BINARY_REQUEST_METHODS:
        return 503, b"", {}, unsupported_method_payload(method)

    request_kwargs = {
        "request_method": request_method,
        "url": url,
        "timeout_seconds": timeout_seconds,
        "params": params,
        "headers": headers,
    }
    attempts = retry_attempts(max_retries)
    for attempt in range(attempts):
        result = await _send_binary_retry_attempt(
            request_kwargs=request_kwargs,
            retry_status_codes=retry_status_codes,
            retry_timeout_exceptions=retry_timeout_exceptions,
            attempt=attempt,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )
        if result is not None:
            return result

    return binary_communication_failure_result("exhausted retries")
