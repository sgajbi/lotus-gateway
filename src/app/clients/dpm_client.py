import logging
from typing import Any

from app.clients.dpm_construction_client import DpmConstructionClientMixin
from app.clients.dpm_outcome_review_client import DpmOutcomeReviewClientMixin
from app.clients.dpm_pm_operating_quality_client import DpmPmOperatingQualityClientMixin
from app.clients.dpm_proof_pack_client import DpmProofPackClientMixin
from app.clients.dpm_wave_client import DpmWaveClientMixin
from app.clients.observed_fanout import request_observed_binary_fanout, request_observed_fanout
from app.clients.upstream_headers import build_upstream_headers

logger = logging.getLogger("analytics_ui.gateway")

_MANAGE_CAPABILITIES_CONSUMERS = {
    "lotus-gateway",
    "lotus-performance",
    "lotus-manage",
    "UI",
    "UNKNOWN",
}


class DpmClient(
    DpmConstructionClientMixin,
    DpmProofPackClientMixin,
    DpmOutcomeReviewClientMixin,
    DpmPmOperatingQualityClientMixin,
    DpmWaveClientMixin,
):
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.2,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds

    async def list_runs(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/runs",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.runs.list",
        )

    async def get_supportability_summary(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/api/v1/rebalance/supportability/summary",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.supportability.summary",
        )

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
            headers=self._headers(correlation_id),
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
            headers=self._headers(correlation_id),
            operation="manage.rebalance.portfolio_memory.search",
        )

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        manage_consumer_system = (
            consumer_system
            if consumer_system in _MANAGE_CAPABILITIES_CONSUMERS
            else "lotus-gateway"
        )
        return await self._get(
            "/api/v1/integration/capabilities",
            params={"consumer_system": manage_consumer_system, "tenant_id": tenant_id},
            headers=self._headers(correlation_id),
            operation="manage.integration.capabilities",
        )

    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        return build_upstream_headers(correlation_id, extras=extras)

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        return await request_observed_fanout(
            logger=logger,
            service="lotus-manage",
            operation=operation,
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
        )

    async def _get_binary_text(
        self,
        path: str,
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, str, dict[str, Any]]:
        (
            status_code,
            content,
            _response_headers,
            error_payload,
        ) = await request_observed_binary_fanout(
            logger=logger,
            service="lotus-manage",
            operation=operation,
            method="GET",
            url=f"{self._base_url}{path}",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params={},
            headers=headers,
        )
        return status_code, content.decode("utf-8", errors="replace"), error_payload

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        return await request_observed_fanout(
            logger=logger,
            service="lotus-manage",
            operation=operation,
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
            json_body=body,
        )

    async def _put(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        return await request_observed_fanout(
            logger=logger,
            service="lotus-manage",
            operation=operation,
            method="PUT",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
            json_body=body,
        )
