import httpx

_RETRYABLE_REQUEST_ERROR_TYPES = (
    httpx.TimeoutException,
    httpx.NetworkError,
    httpx.RemoteProtocolError,
)


def retry_attempts(max_retries: int) -> int:
    return max(0, max_retries) + 1


def retry_delay(backoff_seconds: float, attempt: int) -> float:
    bounded_backoff = backoff_seconds if backoff_seconds > 0.0 else 0.0
    return bounded_backoff * (2.0**attempt)


def should_retry_status(
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


def should_retry_request_error(
    *,
    exc: httpx.RequestError,
    retry_timeout_exceptions: bool,
    attempt: int,
    max_retries: int,
) -> bool:
    if not is_retryable_request_error(exc):
        return False
    if isinstance(exc, httpx.TimeoutException) and not retry_timeout_exceptions:
        return False
    return attempt < max_retries


def is_retryable_request_error(exc: httpx.RequestError) -> bool:
    """Return whether an HTTPX request error can safely be retried."""

    return isinstance(exc, _RETRYABLE_REQUEST_ERROR_TYPES)
