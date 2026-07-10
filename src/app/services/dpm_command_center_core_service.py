from typing import Any

from app.contracts.dpm_command_center import DpmCommandCenterGatewayResponse
from app.services.dpm_client_protocols import DpmCommandCenterClient
from app.services.dpm_command_center_response import compose_command_center_response


class DpmCommandCenterCoreServiceMixin:
    _dpm_client: DpmCommandCenterClient

    async def get_command_center(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_command_center(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def run_monitoring_once(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.run_monitoring_once(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_monitoring_runs(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_monitoring_runs(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_monitoring_run(
        self,
        monitoring_run_id: str,
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_monitoring_run(
            monitoring_run_id=monitoring_run_id,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_monitoring_exceptions(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_monitoring_exceptions(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def resolve_monitoring_exception(
        self,
        exception_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.resolve_monitoring_exception(
            exception_id=exception_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_mandate_by_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_mandate_by_portfolio(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_mandate(
        self,
        mandate_id: str,
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_mandate(
            mandate_id=mandate_id,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_mandate_health(
        self,
        mandate_id: str,
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_mandate_health(
            mandate_id=mandate_id,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_mandate_diff(
        self,
        mandate_id: str,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_mandate_diff(
            mandate_id=mandate_id,
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    def _compose_command_center_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        return compose_command_center_response(upstream_status, upstream_payload, correlation_id)
