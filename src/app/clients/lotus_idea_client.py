import logging
from typing import Any

from app.clients.observed_fanout import request_observed_fanout
from app.clients.upstream_headers import build_upstream_headers

logger = logging.getLogger("analytics_ui.gateway")


class LotusIdeaClient:
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

    async def get_advisor_review_queue(
        self,
        *,
        evaluated_at_utc: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await request_observed_fanout(
            logger=logger,
            service="lotus-idea",
            operation="idea.review-queues.advisor",
            method="GET",
            url=f"{self._base_url}/api/v1/review-queues/advisor",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params={"evaluatedAtUtc": evaluated_at_utc},
            headers=self._idea_headers(caller_headers, correlation_id),
        )

    async def get_candidate_detail(
        self,
        *,
        candidate_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await request_observed_fanout(
            logger=logger,
            service="lotus-idea",
            operation="idea.candidates.detail",
            method="GET",
            url=f"{self._base_url}/api/v1/idea-candidates/{candidate_id}",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=self._idea_headers(caller_headers, correlation_id),
        )

    def _idea_headers(
        self,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> dict[str, str]:
        return build_upstream_headers(
            correlation_id,
            extras={"X-Caller-Service": "lotus-gateway"},
            caller_headers=caller_headers,
        )
