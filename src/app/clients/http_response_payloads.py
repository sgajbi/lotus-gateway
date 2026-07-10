from typing import Any

import httpx


def response_payload(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text}
    if isinstance(payload, dict):
        return payload
    return {"detail": payload}


def unsupported_method_payload(method: str) -> dict[str, str]:
    request_method = method.upper() or "<blank>"
    return {"detail": f"unsupported upstream HTTP method: {request_method}"}


def communication_failure_payload(reason: str) -> dict[str, str]:
    return {"detail": f"upstream communication failure: {reason}"}


def communication_failure_result(reason: str) -> tuple[int, dict[str, str]]:
    return 503, communication_failure_payload(reason)


def binary_communication_failure_result(
    reason: str,
) -> tuple[int, bytes, dict[str, str], dict[str, str]]:
    return 503, b"", {}, communication_failure_payload(reason)
