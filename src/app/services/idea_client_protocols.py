from typing import Any, Protocol


class IdeaClient(Protocol):
    async def get_advisor_review_queue(
        self,
        *,
        evaluated_at_utc: str,
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
