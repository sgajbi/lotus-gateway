from typing import Any

from app.contracts.dpm_command_center import DpmPmOperatingQualityGatewayResponse
from app.services.dpm_client_protocols import DpmCommandCenterClient
from app.services.dpm_pm_operating_quality_response import compose_pm_operating_quality_response


class DpmPmOperatingQualitySummaryInvocationServiceMixin:
    _dpm_client: DpmCommandCenterClient

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
