from typing import Any

from app.contracts.dpm_command_center import DpmPmOperatingQualityGatewayResponse
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_client_protocols import DpmCommandCenterClient
from app.services.dpm_pm_operating_quality_response import compose_pm_operating_quality_response
from app.services.dpm_pm_operating_quality_summary_service import (
    DpmPmOperatingQualitySummaryServiceMixin,
)


class DpmPmOperatingQualityServiceMixin(DpmPmOperatingQualitySummaryServiceMixin):
    _dpm_client: DpmCommandCenterClient
    _lotus_ai_client: LotusAiWorkflowClient | None

    async def preview_pm_operating_quality_score_run(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.preview_pm_operating_quality_score_run(
            body=body,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def create_pm_operating_quality_score_run(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.create_pm_operating_quality_score_run(
            body=body,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def preview_pm_operating_quality_fairness_analysis(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.preview_pm_operating_quality_fairness_analysis(
            body=body,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def create_pm_operating_quality_fairness_analysis(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.create_pm_operating_quality_fairness_analysis(
            body=body,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_pm_operating_quality_fairness_analyses(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.list_pm_operating_quality_fairness_analyses(
            params=filters,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_pm_operating_quality_fairness_analysis(
        self,
        fairness_analysis_id: str,
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_pm_operating_quality_fairness_analysis(
            fairness_analysis_id=fairness_analysis_id,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def preview_pm_operating_quality_review_action(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.preview_pm_operating_quality_review_action(
            body=body,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def create_pm_operating_quality_review_action(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.create_pm_operating_quality_review_action(
            body=body,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_pm_operating_quality_review_actions(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.list_pm_operating_quality_review_actions(
            params=filters,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_pm_operating_quality_review_action(
        self,
        review_action_id: str,
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_pm_operating_quality_review_action(
            review_action_id=review_action_id,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def preview_pm_operating_quality_summary_invocation(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.preview_pm_operating_quality_summary_invocation(
            body=body,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def create_pm_operating_quality_summary_invocation(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.create_pm_operating_quality_summary_invocation(
            body=body,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_pm_operating_quality_summary_invocations(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.list_pm_operating_quality_summary_invocations(
            params=filters,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_pm_operating_quality_summary_invocation(
        self,
        summary_invocation_id: str,
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_pm_operating_quality_summary_invocation(
            summary_invocation_id=summary_invocation_id,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_pm_operating_quality_score_runs(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.list_pm_operating_quality_score_runs(
            params=filters,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_pm_operating_quality_score_run(
        self,
        score_run_id: str,
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_pm_operating_quality_score_run(
            score_run_id=score_run_id,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def put_pm_operating_quality_policy(
        self,
        policy_id: str,
        policy_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.put_pm_operating_quality_policy(
            policy_id=policy_id,
            policy_version=policy_version,
            body=body,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_pm_operating_quality_policies(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.list_pm_operating_quality_policies(
            params=filters,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_pm_operating_quality_policy(
        self,
        policy_id: str,
        policy_version: str,
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_pm_operating_quality_policy(
            policy_id=policy_id,
            policy_version=policy_version,
            correlation_id=correlation_id,
        )
        return compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )
