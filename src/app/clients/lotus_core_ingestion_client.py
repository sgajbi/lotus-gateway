import logging
from typing import Any

from app.clients.observed_fanout import request_observed_fanout
from app.clients.upstream_headers import build_upstream_headers

LOGGER = logging.getLogger("analytics_ui.gateway")


class LotusCoreIngestionClient:
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

    async def ingest_portfolio_bundle(
        self,
        body: dict[str, Any],
        correlation_id: str,
        idempotency_key: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/ingest/portfolio-bundle"
        # Ingestion is a Core WRITE: the ambient caller-presented fence must not
        # scope a mutation (a caller could select another tenant's write
        # partition), so these calls carry no ambient tenant. Core's fail-closed
        # ingress refuses the unadmitted write until the intake routes admit
        # tenant authority explicitly (tracked on the tenant-propagation issue).
        headers = build_upstream_headers(
            correlation_id,
            extras={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
        )
        return await request_observed_fanout(
            logger=LOGGER,
            service="lotus-core",
            operation="core.ingest.portfolio-bundle.create",
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=body,
            headers=headers,
        )

    async def preview_upload(
        self,
        entity_type: str,
        filename: str,
        content: bytes,
        sample_size: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._upload(
            "/ingest/uploads/preview",
            entity_type=entity_type,
            filename=filename,
            content=content,
            extra_data={"sample_size": str(sample_size)},
            correlation_id=correlation_id,
        )

    async def commit_upload(
        self,
        entity_type: str,
        filename: str,
        content: bytes,
        allow_partial: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._upload(
            "/ingest/uploads/commit",
            entity_type=entity_type,
            filename=filename,
            content=content,
            extra_data={"allow_partial": "true" if allow_partial else "false"},
            correlation_id=correlation_id,
        )

    async def _upload(
        self,
        path: str,
        entity_type: str,
        filename: str,
        content: bytes,
        extra_data: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        headers = build_upstream_headers(correlation_id)
        form_data = {"entity_type": entity_type, **extra_data}
        files = {"file": (filename, content)}
        operation = (
            "core.ingest.uploads.preview"
            if path.endswith("/preview")
            else "core.ingest.uploads.commit"
        )
        return await request_observed_fanout(
            logger=LOGGER,
            service="lotus-core",
            operation=operation,
            method="POST",
            url=f"{self._base_url}{path}",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            data=form_data,
            files=files,
            headers=headers,
        )
