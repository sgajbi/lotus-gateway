from typing import Any

from app.clients.http_resilience import request_binary_with_retry, request_with_retry
from app.middleware.correlation import propagation_headers


class ArchiveClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.2,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds

    async def get_document_metadata(
        self,
        *,
        document_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
        current: bool = False,
    ) -> tuple[int, dict[str, Any]]:
        suffix = "/current" if current else ""
        url = f"{self._base_url}/documents/{document_id}{suffix}"
        headers = self._archive_headers(caller_headers, correlation_id)
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
        )

    async def download_document(
        self,
        *,
        document_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, bytes, dict[str, str], dict[str, Any]]:
        url = f"{self._base_url}/documents/{document_id}/download"
        headers = self._archive_headers(caller_headers, correlation_id)
        return await request_binary_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
        )

    def _archive_headers(
        self,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> dict[str, str]:
        headers = propagation_headers(correlation_id)
        headers.update(
            {
                "X-Caller-Service": "lotus-gateway",
                "X-Actor-Type": caller_headers.get("X-Role", "user"),
                "X-Actor-Id": caller_headers["X-Actor-Id"],
                "X-Tenant-Id": caller_headers["X-Tenant-Id"],
                "X-Region": caller_headers["X-Region"],
            }
        )
        if booking_center_code := caller_headers.get("X-Booking-Center-Code"):
            headers["X-Booking-Center-Code"] = booking_center_code
        return headers
