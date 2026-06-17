from typing import Any


class DpmPmOperatingQualityClientMixin:
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

    async def preview_pm_operating_quality_score_run(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/pm-operating-quality/score-runs/preview",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.score_runs.preview",
        )

    async def create_pm_operating_quality_score_run(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/pm-operating-quality/score-runs",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.score_runs.create",
        )

    async def preview_pm_operating_quality_fairness_analysis(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/pm-operating-quality/fairness-analyses/preview",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.fairness_analyses.preview",
        )

    async def create_pm_operating_quality_fairness_analysis(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/pm-operating-quality/fairness-analyses",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.fairness_analyses.create",
        )

    async def list_pm_operating_quality_fairness_analyses(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/pm-operating-quality/fairness-analyses",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.fairness_analyses.list",
        )

    async def get_pm_operating_quality_fairness_analysis(
        self,
        fairness_analysis_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/pm-operating-quality/fairness-analyses/{fairness_analysis_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.fairness_analyses.get",
        )

    async def preview_pm_operating_quality_review_action(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/pm-operating-quality/review-actions/preview",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.review_actions.preview",
        )

    async def create_pm_operating_quality_review_action(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/pm-operating-quality/review-actions",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.review_actions.create",
        )

    async def list_pm_operating_quality_review_actions(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/pm-operating-quality/review-actions",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.review_actions.list",
        )

    async def get_pm_operating_quality_review_action(
        self,
        review_action_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/pm-operating-quality/review-actions/{review_action_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.review_actions.get",
        )

    async def preview_pm_operating_quality_summary_invocation(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/pm-operating-quality/summary-invocations/preview",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.summary_invocations.preview",
        )

    async def create_pm_operating_quality_summary_invocation(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/pm-operating-quality/summary-invocations",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.summary_invocations.create",
        )

    async def list_pm_operating_quality_summary_invocations(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/pm-operating-quality/summary-invocations",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.summary_invocations.list",
        )

    async def get_pm_operating_quality_summary_invocation(
        self,
        summary_invocation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/pm-operating-quality/summary-invocations/{summary_invocation_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.summary_invocations.get",
        )

    async def list_pm_operating_quality_score_runs(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/pm-operating-quality/score-runs",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.score_runs.list",
        )

    async def get_pm_operating_quality_score_run(
        self,
        score_run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/pm-operating-quality/score-runs/{score_run_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.score_runs.get",
        )

    async def put_pm_operating_quality_policy(
        self,
        policy_id: str,
        policy_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._put(
            (
                "/api/v1/rebalance/pm-operating-quality/policies/"
                f"{policy_id}/versions/{policy_version}"
            ),
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.policies.put",
        )

    async def list_pm_operating_quality_policies(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/pm-operating-quality/policies",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.policies.list",
        )

    async def get_pm_operating_quality_policy(
        self,
        policy_id: str,
        policy_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            (
                "/api/v1/rebalance/pm-operating-quality/policies/"
                f"{policy_id}/versions/{policy_version}"
            ),
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.pm_operating_quality.policies.get",
        )
