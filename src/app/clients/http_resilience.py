import asyncio
from typing import Any

import httpx


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
    attempts = _retry_attempts(max_retries)
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(
                timeout=timeout_seconds,
                follow_redirects=True,
            ) as client:
                request_method = method.upper()
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
                return 503, {"detail": f"upstream communication failure: {exc.__class__.__name__}"}
            if attempt >= max_retries:
                return 503, {"detail": f"upstream communication failure: {exc.__class__.__name__}"}
            await asyncio.sleep(_retry_delay(backoff_seconds, attempt))
        except httpx.RequestError as exc:
            if attempt >= max_retries:
                return 503, {"detail": f"upstream communication failure: {exc.__class__.__name__}"}
            await asyncio.sleep(_retry_delay(backoff_seconds, attempt))

    return 503, {"detail": "upstream communication failure: exhausted retries"}


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
    attempts = _retry_attempts(max_retries)
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(
                timeout=timeout_seconds,
                follow_redirects=True,
            ) as client:
                if method.upper() == "GET":
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
                return (
                    503,
                    b"",
                    {},
                    {"detail": f"upstream communication failure: {exc.__class__.__name__}"},
                )
            if attempt >= max_retries:
                return (
                    503,
                    b"",
                    {},
                    {"detail": f"upstream communication failure: {exc.__class__.__name__}"},
                )
            await asyncio.sleep(_retry_delay(backoff_seconds, attempt))
        except httpx.RequestError as exc:
            if attempt >= max_retries:
                return (
                    503,
                    b"",
                    {},
                    {"detail": f"upstream communication failure: {exc.__class__.__name__}"},
                )
            await asyncio.sleep(_retry_delay(backoff_seconds, attempt))

    return 503, b"", {}, {"detail": "upstream communication failure: exhausted retries"}
