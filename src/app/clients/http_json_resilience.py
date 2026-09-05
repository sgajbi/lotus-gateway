from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import httpx

from app.clients.http_response_payloads import (
    communication_failure_result,
    response_payload,
    unsupported_method_payload,
)
from app.clients.http_retry_policy import (
    is_retryable_request_error,
    retry_attempts,
    retry_delay,
    should_retry_request_error,
    should_retry_status,
)

_JSON_REQUEST_METHODS = frozenset({"GET", "POST", "PUT"})


class RequestFailureKind(StrEnum):
    TRANSPORT = "transport"
    TIMEOUT = "timeout"
    TERMINAL_REQUEST_ERROR = "terminal_request_error"
    UNSUPPORTED_METHOD = "unsupported_method"
    RETRIES_EXHAUSTED = "retries_exhausted"


@dataclass(frozen=True)
class JsonRequestOutcome:
    status_code: int
    payload: dict[str, Any]
    failure_kind: RequestFailureKind | None = None

    @property
    def is_transient_transport_failure(self) -> bool:
        return self.failure_kind in {
            RequestFailureKind.TRANSPORT,
            RequestFailureKind.TIMEOUT,
        }

    def as_result(self) -> tuple[int, dict[str, Any]]:
        return self.status_code, self.payload


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


async def _retry_or_return_json_response(
    *,
    response: httpx.Response,
    retry_status_codes: set[int] | None,
    attempt: int,
    max_retries: int,
    backoff_seconds: float,
) -> JsonRequestOutcome | None:
    if should_retry_status(
        response_status_code=response.status_code,
        retry_status_codes=retry_status_codes,
        attempt=attempt,
        max_retries=max_retries,
    ):
        await _sleep_before_retry(backoff_seconds, attempt)
        return None
    return JsonRequestOutcome(response.status_code, response_payload(response))


def _request_error_failure_kind(exc: httpx.RequestError) -> RequestFailureKind:
    if isinstance(exc, httpx.TimeoutException):
        return RequestFailureKind.TIMEOUT
    if is_retryable_request_error(exc):
        return RequestFailureKind.TRANSPORT
    return RequestFailureKind.TERMINAL_REQUEST_ERROR


async def _retry_or_return_request_error(
    *,
    exc: httpx.RequestError,
    retry_timeout_exceptions: bool,
    retry_ambiguous_request_errors: bool,
    attempt: int,
    max_retries: int,
    backoff_seconds: float,
) -> JsonRequestOutcome | None:
    if should_retry_request_error(
        exc=exc,
        retry_timeout_exceptions=retry_timeout_exceptions,
        retry_ambiguous_request_errors=retry_ambiguous_request_errors,
        attempt=attempt,
        max_retries=max_retries,
    ):
        await _sleep_before_retry(backoff_seconds, attempt)
        return None
    status_code, payload = communication_failure_result(exc.__class__.__name__)
    return JsonRequestOutcome(
        status_code=status_code,
        payload=payload,
        failure_kind=_request_error_failure_kind(exc),
    )


async def _send_json_retry_attempt(
    *,
    request_kwargs: dict[str, Any],
    retry_status_codes: set[int] | None,
    retry_timeout_exceptions: bool,
    retry_ambiguous_request_errors: bool,
    attempt: int,
    max_retries: int,
    backoff_seconds: float,
) -> JsonRequestOutcome | None:
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
            retry_ambiguous_request_errors=retry_ambiguous_request_errors,
            attempt=attempt,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )


async def _sleep_before_retry(backoff_seconds: float, attempt: int) -> None:
    await asyncio.sleep(retry_delay(backoff_seconds, attempt))


def _json_request_kwargs(
    *,
    request_method: str,
    url: str,
    timeout_seconds: float,
    params: dict[str, Any] | None,
    headers: dict[str, str] | None,
    json_body: dict[str, Any] | None,
    data: dict[str, Any] | None,
    files: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "request_method": request_method,
        "url": url,
        "timeout_seconds": timeout_seconds,
        "params": params,
        "headers": headers,
        "json_body": json_body,
        "data": data,
        "files": files,
    }


async def _execute_json_request(
    *,
    request_kwargs: dict[str, Any],
    retry_status_codes: set[int] | None,
    retry_timeout_exceptions: bool,
    retry_ambiguous_request_errors: bool,
    max_retries: int,
    backoff_seconds: float,
) -> JsonRequestOutcome:
    for attempt in range(retry_attempts(max_retries)):
        result = await _send_json_retry_attempt(
            request_kwargs=request_kwargs,
            retry_status_codes=retry_status_codes,
            retry_timeout_exceptions=retry_timeout_exceptions,
            retry_ambiguous_request_errors=retry_ambiguous_request_errors,
            attempt=attempt,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )
        if result is not None:
            return result
    status_code, payload = communication_failure_result("exhausted retries")
    return JsonRequestOutcome(
        status_code=status_code,
        payload=payload,
        failure_kind=RequestFailureKind.RETRIES_EXHAUSTED,
    )


async def request_with_retry_outcome(
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
    retry_ambiguous_request_errors: bool = True,
) -> JsonRequestOutcome:
    request_method = method.upper()
    if request_method not in _JSON_REQUEST_METHODS:
        return JsonRequestOutcome(
            status_code=503,
            payload=unsupported_method_payload(method),
            failure_kind=RequestFailureKind.UNSUPPORTED_METHOD,
        )
    request_kwargs = _json_request_kwargs(
        request_method=request_method,
        url=url,
        timeout_seconds=timeout_seconds,
        params=params,
        headers=headers,
        json_body=json_body,
        data=data,
        files=files,
    )
    return await _execute_json_request(
        request_kwargs=request_kwargs,
        retry_status_codes=retry_status_codes,
        retry_timeout_exceptions=retry_timeout_exceptions,
        retry_ambiguous_request_errors=retry_ambiguous_request_errors,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
    )
