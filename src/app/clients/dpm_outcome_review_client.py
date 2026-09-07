from typing import Any

from app.clients.dpm_client_call_surface import DpmClientCallSurfaceMixin


class DpmOutcomeReviewClientMixin(DpmClientCallSurfaceMixin):
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
        idempotency_key: str,
        correlation_id: str,
        caller_headers: dict[str, str],
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/outcome-reviews",
            body=body,
            headers=self._headers(
                correlation_id,
                {**caller_headers, "Idempotency-Key": idempotency_key},
            ),
            operation="manage.rebalance.outcome_reviews.create",
        )

    async def list_outcome_reviews(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = self._clean_params(params)
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
        tenant_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/outcome-reviews/{outcome_review_id}/report-input",
            params={"tenant_id": tenant_id},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.outcome_reviews.report_input",
        )

    async def get_outcome_review_ai_evidence_input(
        self,
        outcome_review_id: str,
        correlation_id: str,
        tenant_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/outcome-reviews/{outcome_review_id}/ai-evidence-input",
            params={"tenant_id": tenant_id},
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
        cleaned_params = self._clean_params(params)
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}/outcome-reviews",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.outcome_reviews",
        )
