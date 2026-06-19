from typing import Any

from app.contracts.dpm_waves import DpmCampaignWorkflowGatewayResponse, DpmWaveErrorDetail
from app.services.dpm_wave_client_protocols import DpmWaveClient
from app.services.upstream_envelope import (
    build_product_safe_upstream_status_payload_gateway_envelope,
)


class DpmWaveCampaignWorkflowMixin:
    _dpm_client: DpmWaveClient

    async def get_campaign_operating_queue(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_campaign_operating_queue(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def get_campaign_approval_inbox(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_campaign_approval_inbox(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def get_campaign_workflow_board(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_campaign_workflow_board(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def get_campaign_assignment_plan(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_campaign_assignment_plan(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def get_campaign_workflow_automation(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_campaign_workflow_automation(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def list_campaign_approval_decisions(
        self,
        campaign_id: str,
        campaign_version: str,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_campaign_approval_decisions(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def create_campaign_approval_decision(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.create_campaign_approval_decision(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def list_campaign_assignment_actions(
        self,
        campaign_id: str,
        campaign_version: str,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_campaign_assignment_actions(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def create_campaign_assignment_action(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.create_campaign_assignment_action(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def list_campaign_assignment_tasks(
        self,
        campaign_id: str,
        campaign_version: str,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_campaign_assignment_tasks(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def create_campaign_assignment_task(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.create_campaign_assignment_task(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def transition_campaign_assignment_task(
        self,
        campaign_id: str,
        campaign_version: str,
        task_ref: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.transition_campaign_assignment_task(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            task_ref=task_ref,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def list_campaign_maker_checker_controls(
        self,
        campaign_id: str,
        campaign_version: str,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.list_campaign_maker_checker_controls(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    async def create_campaign_maker_checker_control(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.create_campaign_maker_checker_control(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_workflow_response(
            upstream_status, upstream_payload, correlation_id
        )

    def _compose_campaign_workflow_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignWorkflowGatewayResponse:
        return build_product_safe_upstream_status_payload_gateway_envelope(
            DpmCampaignWorkflowGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            upstream_payload=upstream_payload,
            error_model=DpmWaveErrorDetail,
            error_code="MANAGE_WAVE_UPSTREAM_ERROR",
            default_detail="lotus-manage rebalance-wave request failed",
        )
