from typing import Any, Protocol


class AdvisoryCopilotClient(Protocol):
    async def create_advisory_copilot_evidence_packet(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_advisory_copilot_evidence_packet_from_proposal_version(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisory_copilot_evidence_packet(
        self,
        *,
        evidence_packet_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def run_advisory_copilot_action(
        self,
        *,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisory_copilot_run(
        self,
        *,
        run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def review_advisory_copilot_run(
        self,
        *,
        run_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisory_copilot_supportability(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_advisory_copilot_proposal_version_runs(
        self,
        *,
        proposal_id: str,
        version_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...
