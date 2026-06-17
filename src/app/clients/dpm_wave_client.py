from typing import Any


class DpmWaveClientMixin:
    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        raise NotImplementedError

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _put(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def preview_wave(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/waves/preview",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.preview",
        )

    async def create_wave(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/waves",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="manage.rebalance.waves.create",
        )

    async def list_waves(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/waves",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.list",
        )

    async def get_wave(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.get",
        )

    async def put_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._put(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.put",
        )

    async def list_campaign_definitions(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/waves/campaign-definitions",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.list",
        )

    async def get_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.get",
        )

    async def get_campaign_definition_lifecycle_events(
        self,
        campaign_id: str,
        campaign_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/lifecycle-events",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.lifecycle_events",
        )

    async def get_campaign_definition_preview_readiness(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/preview-readiness",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.preview_readiness",
        )

    async def get_campaign_definition_launch_history(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-history",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.launch_history",
        )

    async def get_campaign_definition_launch_package(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-package",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.launch_package",
        )

    async def launch_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.launch",
        )

    async def retire_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/retire",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.retire",
        )

    async def supersede_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/supersede",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.supersede",
        )

    async def discover_campaigns(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/waves/campaign-discovery",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_discovery",
        )

    async def get_campaign_operating_queue(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_campaign_workflow_read(
            path="/api/v1/rebalance/waves/campaign-operating-queue",
            params=params,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_operating_queue",
        )

    async def get_campaign_approval_inbox(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_campaign_workflow_read(
            path="/api/v1/rebalance/waves/campaign-approval-inbox",
            params=params,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_approval_inbox",
        )

    async def get_campaign_workflow_board(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_campaign_workflow_read(
            path="/api/v1/rebalance/waves/campaign-workflow-board",
            params=params,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_workflow_board",
        )

    async def get_campaign_assignment_plan(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_campaign_workflow_read(
            path="/api/v1/rebalance/waves/campaign-assignment-plan",
            params=params,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_assignment_plan",
        )

    async def get_campaign_workflow_automation(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_campaign_workflow_read(
            path="/api/v1/rebalance/waves/campaign-workflow-automation",
            params=params,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_workflow_automation",
        )

    async def list_campaign_approval_decisions(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_campaign_workflow_read(
            path=self._campaign_definition_workflow_path(
                campaign_id, campaign_version, "approval-decisions"
            ),
            params=params,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_approval_decisions.list",
        )

    async def create_campaign_approval_decision(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_campaign_workflow_write(
            path=self._campaign_definition_workflow_path(
                campaign_id, campaign_version, "approval-decisions"
            ),
            body=body,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_approval_decisions.create",
        )

    async def list_campaign_assignment_actions(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_campaign_workflow_read(
            path=self._campaign_definition_workflow_path(
                campaign_id, campaign_version, "assignment-actions"
            ),
            params=params,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_assignment_actions.list",
        )

    async def create_campaign_assignment_action(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_campaign_workflow_write(
            path=self._campaign_definition_workflow_path(
                campaign_id, campaign_version, "assignment-actions"
            ),
            body=body,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_assignment_actions.create",
        )

    async def list_campaign_assignment_tasks(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_campaign_workflow_read(
            path=self._campaign_definition_workflow_path(
                campaign_id, campaign_version, "assignment-tasks"
            ),
            params=params,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_assignment_tasks.list",
        )

    async def create_campaign_assignment_task(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_campaign_workflow_write(
            path=self._campaign_definition_workflow_path(
                campaign_id, campaign_version, "assignment-tasks"
            ),
            body=body,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_assignment_tasks.create",
        )

    async def transition_campaign_assignment_task(
        self,
        campaign_id: str,
        campaign_version: str,
        task_ref: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_campaign_workflow_write(
            path=(
                self._campaign_definition_workflow_path(
                    campaign_id, campaign_version, "assignment-tasks"
                )
                + f"/{task_ref}/transitions"
            ),
            body=body,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_assignment_tasks.transitions.create",
        )

    async def list_campaign_maker_checker_controls(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_campaign_workflow_read(
            path=self._campaign_definition_workflow_path(
                campaign_id, campaign_version, "maker-checker-controls"
            ),
            params=params,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_maker_checker_controls.list",
        )

    async def create_campaign_maker_checker_control(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_campaign_workflow_write(
            path=self._campaign_definition_workflow_path(
                campaign_id, campaign_version, "maker-checker-controls"
            ),
            body=body,
            correlation_id=correlation_id,
            operation="manage.rebalance.waves.campaign_maker_checker_controls.create",
        )

    async def get_wave_items(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}/items",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.items",
        )

    async def source_check_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/source-check",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.source_check",
        )

    async def simulate_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/simulate",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.simulate",
        )

    async def select_wave_item(
        self,
        wave_id: str,
        wave_item_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/items/{wave_item_id}/select",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.items.select",
        )

    async def approve_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/approve",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.approve",
        )

    async def stage_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/stage",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.stage",
        )

    async def handoff_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/handoff",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.handoff",
        )

    async def cancel_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/cancel",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.cancel",
        )

    async def get_wave_proof_pack_posture(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}/proof-pack",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.proof_pack",
        )

    async def get_wave_supportability(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}/supportability",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.supportability",
        )

    async def get_wave_report_input(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}/report-input",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.report_input",
        )

    async def _get_campaign_workflow_read(
        self,
        path: str,
        params: dict[str, Any],
        correlation_id: str,
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            path,
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation=operation,
        )

    async def _post_campaign_workflow_write(
        self,
        path: str,
        body: dict[str, Any],
        correlation_id: str,
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            path,
            body=body,
            headers=self._headers(correlation_id),
            operation=operation,
        )

    def _campaign_definition_workflow_path(
        self,
        campaign_id: str,
        campaign_version: str,
        suffix: str,
    ) -> str:
        return (
            "/api/v1/rebalance/waves/campaign-definitions/"
            f"{campaign_id}/versions/{campaign_version}/{suffix}"
        )
