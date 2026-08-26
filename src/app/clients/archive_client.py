import logging
from typing import Any, Final

from app.clients.observed_fanout import (
    request_observed_binary_fanout,
    request_observed_fanout,
)
from app.clients.upstream_headers import build_archive_caller_headers

logger = logging.getLogger("analytics_ui.gateway")

_ACCESS_PREFLIGHT_MAX_RETRIES: Final = 0


class ArchiveClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        access_preflight_timeout_seconds: float,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.2,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._access_preflight_timeout = access_preflight_timeout_seconds

    async def preflight_document_access(
        self,
        *,
        document_ids: list[str],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        headers = self._archive_headers(caller_headers, correlation_id)
        return await request_observed_fanout(
            logger=logger,
            service="lotus-archive",
            operation="archive.documents.access-preflight",
            method="POST",
            url=f"{self._base_url}/documents/access-preflight",
            timeout_seconds=self._access_preflight_timeout,
            total_deadline_seconds=self._access_preflight_timeout,
            max_retries=_ACCESS_PREFLIGHT_MAX_RETRIES,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
            json_body={"document_ids": document_ids},
        )

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
        return await request_observed_fanout(
            logger=logger,
            service="lotus-archive",
            operation=(
                "archive.documents.current-metadata" if current else "archive.documents.metadata"
            ),
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
        return await request_observed_binary_fanout(
            logger=logger,
            service="lotus-archive",
            operation="archive.documents.download",
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
        return build_archive_caller_headers(
            correlation_id=correlation_id,
            caller_headers=caller_headers,
        )
