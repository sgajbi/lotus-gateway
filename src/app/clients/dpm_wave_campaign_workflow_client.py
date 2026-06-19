from typing import Any

from app.clients.dpm_wave_client_base import DpmWaveClientBaseMixin


class DpmWaveCampaignWorkflowClientMixin(DpmWaveClientBaseMixin):
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
