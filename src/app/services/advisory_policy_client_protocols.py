from typing import Any, Protocol


class AdvisoryPolicyClient(Protocol):
    async def list_policy_packs(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def validate_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def activate_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_policy_evaluation(
        self,
        *,
        proposal_id: str,
        proposal_version_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_review_queue(
        self,
        *,
        evaluation_status: str | None,
        portfolio_id: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_evaluation(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def replay_policy_evaluation(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def record_policy_evaluation_event(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_evaluation_lineage(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_sign_off_package(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_evaluation_workflow(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def record_policy_sign_off_decision(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def request_policy_report_package(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def request_policy_ai_evidence(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...
