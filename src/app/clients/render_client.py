import logging
from typing import Any

from app.clients.observed_fanout import request_observed_fanout
from app.middleware.correlation import propagation_headers

logger = logging.getLogger("analytics_ui.gateway")


class RenderClient:
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

    async def get_metadata(self, *, correlation_id: str) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/metadata"
        headers = propagation_headers(correlation_id)
        return await request_observed_fanout(
            logger=logger,
            service="lotus-render",
            operation="render.metadata",
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
        )
