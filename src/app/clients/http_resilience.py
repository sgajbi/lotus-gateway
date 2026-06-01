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

    attempts = _retry_attempts(max_retries)
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(
                timeout=timeout_seconds,
                follow_redirects=True,
            ) as client:
                if request_method == "GET":
                    response = await client.get(url, params=params, headers=headers)
                elif request_method == "PUT":
                    response = await client.put(url, headers=headers, json=json_body)
                else:
                    response = await client.post(
                        url,
                        params=params,
                        headers=headers,
                        json=json_body,
                        data=data,
                        files=files,
                    )

            should_retry_status = retry_status_codes and response.status_code in retry_status_codes
            if should_retry_status and attempt < max_retries:
                await asyncio.sleep(_retry_delay(backoff_seconds, attempt))
                continue
            return response.status_code, _response_payload(response)
        except httpx.TimeoutException as exc:
            if not retry_timeout_exceptions:
                return _communication_failure_result(exc.__class__.__name__)
            if attempt >= max_retries:
                return _communication_failure_result(exc.__class__.__name__)
            await asyncio.sleep(_retry_delay(backoff_seconds, attempt))
        except httpx.RequestError as exc:
            if attempt >= max_retries:
                return _communication_failure_result(exc.__class__.__name__)
            await asyncio.sleep(_retry_delay(backoff_seconds, attempt))

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
            async with httpx.AsyncClient(
                timeout=timeout_seconds,
                follow_redirects=True,
            ) as client:
                if request_method == "GET":
                    response = await client.get(url, params=params, headers=headers)
                else:
                    response = await client.post(url, headers=headers)

            should_retry_status = retry_status_codes and response.status_code in retry_status_codes
            if should_retry_status and attempt < max_retries:
                await asyncio.sleep(_retry_delay(backoff_seconds, attempt))
                continue
            error_payload: dict[str, Any] = {}
            if response.status_code >= 400:
                error_payload = _response_payload(response)
            return response.status_code, response.content, dict(response.headers), error_payload
        except httpx.TimeoutException as exc:
            if not retry_timeout_exceptions:
                return _binary_communication_failure_result(exc.__class__.__name__)
            if attempt >= max_retries:
                return _binary_communication_failure_result(exc.__class__.__name__)
            await asyncio.sleep(_retry_delay(backoff_seconds, attempt))
        except httpx.RequestError as exc:
            if attempt >= max_retries:
                return _binary_communication_failure_result(exc.__class__.__name__)
            await asyncio.sleep(_retry_delay(backoff_seconds, attempt))

    return _binary_communication_failure_result("exhausted retries")
