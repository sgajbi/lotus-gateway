from typing import Any

from app.clients.manage_write_authority import build_manage_pm_quality_read_headers


class DpmCommandCenterClientMixin:
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

    async def get_command_center(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/dpm/command-center",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.dpm.command_center.get",
        )

    async def run_monitoring_once(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/dpm/monitoring/run-once",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.dpm.monitoring.run_once",
        )

    async def list_monitoring_runs(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/dpm/monitoring/runs",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.dpm.monitoring.runs.list",
        )

    async def get_monitoring_run(
        self,
        monitoring_run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/dpm/monitoring/runs/{monitoring_run_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.dpm.monitoring.runs.get",
        )

    async def list_monitoring_exceptions(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/dpm/exceptions",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.dpm.exceptions.list",
        )

    async def resolve_monitoring_exception(
        self,
        exception_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/dpm/exceptions/{exception_id}/resolve",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.dpm.exceptions.resolve",
        )

    async def get_mandate_by_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/mandates/by-portfolio/{portfolio_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.mandates.by_portfolio.get",
        )

    async def get_mandate(
        self,
        mandate_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/mandates/{mandate_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.mandates.get",
        )

    async def get_mandate_health(
        self,
        mandate_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/mandates/{mandate_id}/health",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.mandates.health.get",
        )

    async def get_mandate_diff(
        self,
        mandate_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            f"/api/v1/mandates/{mandate_id}/diff",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.mandates.diff.get",
        )

    async def get_portfolio_memory(
        self,
        portfolio_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            f"/api/v1/rebalance/portfolio-memory/{portfolio_id}",
            params=cleaned_params,
            headers=build_manage_pm_quality_read_headers(correlation_id),
            operation="manage.rebalance.portfolio_memory.get",
        )

    async def search_portfolio_memory(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/portfolio-memory/search",
            params=cleaned_params,
            headers=build_manage_pm_quality_read_headers(correlation_id),
            operation="manage.rebalance.portfolio_memory.search",
        )
