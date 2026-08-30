import logging
from typing import Any

from app.clients.observed_fanout import request_observed_fanout
from app.clients.upstream_headers import (
    build_idempotent_upstream_headers,
    build_upstream_headers,
)

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
        evaluated_at_utc: str | None,
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
            params=({"evaluatedAtUtc": evaluated_at_utc} if evaluated_at_utc is not None else {}),
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

    async def record_candidate_review_action(
        self,
        *,
        candidate_id: str,
        body: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._record_candidate_action(
            operation="idea.candidates.review-actions.record",
            candidate_id=candidate_id,
            action_path="review-actions",
            body=body,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            causation_id=causation_id,
        )

    async def record_candidate_feedback(
        self,
        *,
        candidate_id: str,
        body: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._record_candidate_action(
            operation="idea.candidates.feedback.record",
            candidate_id=candidate_id,
            action_path="feedback",
            body=body,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            causation_id=causation_id,
        )

    async def record_candidate_presentation_receipt(
        self,
        *,
        candidate_id: str,
        body: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._record_candidate_action(
            operation="idea.candidates.presentation-receipts.record",
            candidate_id=candidate_id,
            action_path="presentation-receipts",
            body=body,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            causation_id=causation_id,
        )

    async def record_candidate_conversion_intent(
        self,
        *,
        candidate_id: str,
        body: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._record_candidate_action(
            operation="idea.candidates.conversion-intents.record",
            candidate_id=candidate_id,
            action_path="conversion-intents",
            body=body,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            causation_id=causation_id,
        )

    async def _record_candidate_action(
        self,
        *,
        operation: str,
        candidate_id: str,
        action_path: str,
        body: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> tuple[int, dict[str, Any]]:
        return await request_observed_fanout(
            logger=logger,
            service="lotus-idea",
            operation=operation,
            method="POST",
            url=f"{self._base_url}/api/v1/idea-candidates/{candidate_id}/{action_path}",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=self._idea_mutation_headers(
                caller_headers,
                correlation_id,
                idempotency_key=idempotency_key,
                causation_id=causation_id,
            ),
            json_body=body,
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

    def _idea_mutation_headers(
        self,
        caller_headers: dict[str, str],
        correlation_id: str,
        *,
        idempotency_key: str,
        causation_id: str | None,
    ) -> dict[str, str]:
        headers = build_idempotent_upstream_headers(
            correlation_id,
            idempotency_key,
            caller_headers=caller_headers,
        )
        headers["X-Caller-Service"] = "lotus-gateway"
        if causation_id:
            headers["X-Causation-Id"] = causation_id
        return headers
