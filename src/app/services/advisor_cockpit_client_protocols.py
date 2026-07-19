from typing import Any, Protocol


class AdvisorCockpitClient(Protocol):
    async def list_advisor_cockpit_actions(
        self,
        *,
        params: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_advisor_cockpit_preparation_packets(
        self,
        *,
        params: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisor_cockpit_action(
        self,
        *,
        action_item_id: str,
        params: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisor_cockpit_snapshot(
        self,
        *,
        params: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisor_cockpit_supportability(
        self,
        *,
        params: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def acknowledge_advisor_cockpit_action(
        self,
        *,
        action_item_id: str,
        body: dict[str, Any],
        params: dict[str, Any],
        caller_headers: dict[str, str],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def evaluate_advisor_cockpit_house_view_cohort(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...
