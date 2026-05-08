import logging
from typing import Any

from app.clients.observed_fanout import request_observed_binary_fanout, request_observed_fanout
from app.middleware.correlation import propagation_headers

logger = logging.getLogger("analytics_ui.gateway")

_MANAGE_CAPABILITIES_CONSUMERS = {
    "lotus-gateway",
    "lotus-performance",
    "lotus-manage",
    "UI",
    "UNKNOWN",
}


class DpmClient:
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

    async def preview_outcome_review(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/outcome-reviews/preview",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.outcome_reviews.preview",
        )

    async def create_outcome_review(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/outcome-reviews",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.outcome_reviews.create",
        )

    async def list_outcome_reviews(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/outcome-reviews",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.outcome_reviews.list",
        )

    async def get_outcome_review(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/outcome-reviews/{outcome_review_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.outcome_reviews.get",
        )

    async def refresh_outcome_review_sources(
        self,
        outcome_review_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/outcome-reviews/{outcome_review_id}/refresh-sources",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.outcome_reviews.refresh_sources",
        )

    async def get_outcome_review_supportability(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/outcome-reviews/{outcome_review_id}/supportability",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.outcome_reviews.supportability",
        )

    async def get_outcome_review_report_input(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/outcome-reviews/{outcome_review_id}/report-input",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.outcome_reviews.report_input",
        )

    async def get_outcome_review_ai_evidence_input(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/outcome-reviews/{outcome_review_id}/ai-evidence-input",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.outcome_reviews.ai_evidence_input",
        )

    async def get_run_outcome_review(
        self,
        rebalance_run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/runs/{rebalance_run_id}/outcome-review",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.runs.outcome_review",
        )

    async def list_wave_outcome_reviews(
        self,
        wave_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}/outcome-reviews",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.outcome_reviews",
        )

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

    async def generate_construction_alternative_set(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/construction/alternative-sets/generate",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="manage.construction.alternative_sets.generate",
        )

    async def get_construction_alternative_set(
        self,
        alternative_set_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/construction/alternative-sets/{alternative_set_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.construction.alternative_sets.get",
        )

    async def select_construction_alternative(
        self,
        alternative_set_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/construction/alternative-sets/{alternative_set_id}/selections",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.construction.alternative_sets.select",
        )

    async def generate_proof_pack(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/proof-packs",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="manage.rebalance.proof_packs.generate",
        )

    async def get_proof_pack(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/proof-packs/{proof_pack_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proof_packs.get",
        )

    async def get_proof_pack_markdown(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, str, dict[str, Any]]:
        (
            status_code,
            content,
            _response_headers,
            error_payload,
        ) = await request_observed_binary_fanout(
            logger=logger,
            service="lotus-manage",
            operation="manage.rebalance.proof_packs.markdown",
            method="GET",
            url=f"{self._base_url}/api/v1/rebalance/proof-packs/{proof_pack_id}/summary.md",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params={},
            headers=self._headers(correlation_id),
        )
        return status_code, content.decode("utf-8", errors="replace"), error_payload

    async def get_proof_pack_report_input(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/proof-packs/{proof_pack_id}/report-input",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proof_packs.report_input",
        )

    async def get_proof_pack_ai_evidence_input(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/proof-packs/{proof_pack_id}/ai-evidence-input",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proof_packs.ai_evidence_input",
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
        headers = propagation_headers(correlation_id)
        if extras:
            headers.update(extras)
        return headers

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
