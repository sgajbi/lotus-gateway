from typing import Any, Protocol


class DpmWaveClient(Protocol):
    async def preview_wave(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_wave(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_waves(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_wave(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def put_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_campaign_definitions(
        self,
        params: dict[str, Any],
        correlation_id: str,
        tenant_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        correlation_id: str,
        tenant_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_definition_lifecycle_events(
        self,
        campaign_id: str,
        campaign_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_definition_preview_readiness(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_definition_launch_history(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_definition_launch_package(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def launch_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def retire_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def supersede_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def discover_campaigns(
        self,
        params: dict[str, Any],
        correlation_id: str,
        tenant_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_operating_queue(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_approval_inbox(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_workflow_board(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_assignment_plan(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_workflow_automation(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_campaign_approval_decisions(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_campaign_approval_decision(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_campaign_assignment_actions(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_campaign_assignment_action(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_campaign_assignment_tasks(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_campaign_assignment_task(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def transition_campaign_assignment_task(
        self,
        campaign_id: str,
        campaign_version: str,
        task_ref: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_campaign_maker_checker_controls(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_campaign_maker_checker_control(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_wave_items(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def source_check_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def simulate_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def select_wave_item(
        self,
        wave_id: str,
        wave_item_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def approve_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def stage_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def handoff_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def cancel_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_wave_proof_pack_posture(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_wave_supportability(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_wave_report_input(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...
