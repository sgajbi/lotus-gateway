import asyncio
from typing import Any

import httpx

_BINARY_REQUEST_METHODS = frozenset({"GET", "POST"})
_JSON_REQUEST_METHODS = frozenset({"GET", "POST", "PUT"})


def _retry_attempts(max_retries: int) -> int:
    return max(0, max_retries) + 1


def _retry_delay(backoff_seconds: float, attempt: int) -> float:
    bounded_backoff = backoff_seconds if backoff_seconds > 0.0 else 0.0
    return bounded_backoff * (2.0**attempt)


def _response_payload(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text}
    if isinstance(payload, dict):
        return payload
    return {"detail": payload}


def _unsupported_method_payload(method: str) -> dict[str, str]:
    request_method = method.upper() or "<blank>"
    return {"detail": f"unsupported upstream HTTP method: {request_method}"}


def _communication_failure_payload(reason: str) -> dict[str, str]:
    return {"detail": f"upstream communication failure: {reason}"}


def _communication_failure_result(reason: str) -> tuple[int, dict[str, str]]:
    return 503, _communication_failure_payload(reason)


def _binary_communication_failure_result(
    reason: str,
) -> tuple[int, bytes, dict[str, str], dict[str, str]]:
    return 503, b"", {}, _communication_failure_payload(reason)


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


def _should_retry_status(
    *,
    response_status_code: int,
    retry_status_codes: set[int] | None,
    attempt: int,
    max_retries: int,
) -> bool:
    return (
        retry_status_codes is not None
        and response_status_code in retry_status_codes
        and attempt < max_retries
    )


def _should_retry_request_error(
    *,
    exc: httpx.RequestError,
    retry_timeout_exceptions: bool,
    attempt: int,
    max_retries: int,
) -> bool:
    if isinstance(exc, httpx.TimeoutException) and not retry_timeout_exceptions:
        return False
    return attempt < max_retries


async def _sleep_before_retry(backoff_seconds: float, attempt: int) -> None:
    await asyncio.sleep(_retry_delay(backoff_seconds, attempt))


async def _retry_or_return_json_response(
    *,
    response: httpx.Response,
    retry_status_codes: set[int] | None,
    attempt: int,
    max_retries: int,
    backoff_seconds: Any,
) -> tuple[int, dict[str, Any]] | None:
    if _should_retry_status(
        response_status_code=response.status_code,
        retry_status_codes=retry_status_codes,
        attempt=attempt,
        max_retries=max_retries,
    ):
        await _sleep_before_retry(backoff_seconds, attempt)
        return None
    return response.status_code, _response_payload(response)


async def _retry_or_return_request_error(
    *,
    exc: httpx.RequestError,
    retry_timeout_exceptions: bool,
    attempt: int,
    max_retries: int,
    backoff_seconds: Any,
) -> tuple[int, dict[str, str]] | None:
    if not _should_retry_request_error(
        exc=exc,
        retry_timeout_exceptions=retry_timeout_exceptions,
        attempt=attempt,
        max_retries=max_retries,
    ):
        return _communication_failure_result(exc.__class__.__name__)
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
        return 503, _unsupported_method_payload(method)

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
    attempts = _retry_attempts(max_retries)
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

    return _communication_failure_result("exhausted retries")


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
        return 503, b"", {}, _unsupported_method_payload(method)

    attempts = _retry_attempts(max_retries)
    for attempt in range(attempts):
        try:
            response = await _send_binary_request_once(
                request_method=request_method,
                url=url,
                timeout_seconds=timeout_seconds,
                params=params,
                headers=headers,
            )
            if _should_retry_status(
                response_status_code=response.status_code,
                retry_status_codes=retry_status_codes,
                attempt=attempt,
                max_retries=max_retries,
            ):
                await _sleep_before_retry(backoff_seconds, attempt)
                continue
            error_payload: dict[str, Any] = {}
            if response.status_code >= 400:
                error_payload = _response_payload(response)
            return response.status_code, response.content, dict(response.headers), error_payload
        except httpx.RequestError as exc:
            if not _should_retry_request_error(
                exc=exc,
                retry_timeout_exceptions=retry_timeout_exceptions,
                attempt=attempt,
                max_retries=max_retries,
            ):
                return _binary_communication_failure_result(exc.__class__.__name__)
            await _sleep_before_retry(backoff_seconds, attempt)

    return _binary_communication_failure_result("exhausted retries")
