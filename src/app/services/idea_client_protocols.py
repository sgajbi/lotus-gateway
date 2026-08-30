from typing import Any, Protocol


class IdeaClient(Protocol):
    async def get_advisor_review_queue(
        self,
        *,
        evaluated_at_utc: str | None,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_candidate_detail(
        self,
        *,
        candidate_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def record_candidate_review_action(
        self,
        *,
        candidate_id: str,
        body: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def record_candidate_feedback(
        self,
        *,
        candidate_id: str,
        body: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def record_candidate_presentation_receipt(
        self,
        *,
        candidate_id: str,
        body: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def record_candidate_conversion_intent(
        self,
        *,
        candidate_id: str,
        body: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> tuple[int, dict[str, Any]]: ...
