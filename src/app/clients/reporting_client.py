import logging
from typing import Any

from app.clients.observed_fanout import request_observed_fanout
from app.clients.reporting_batch_client import ReportingBatchClientMixin
from app.clients.upstream_headers import (
    build_idempotent_upstream_headers,
    build_upstream_headers,
)

logger = logging.getLogger("analytics_ui.gateway")


class ReportingClient(ReportingBatchClientMixin):
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

    async def get_portfolio_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/aggregations/portfolios/{portfolio_id}"
        params = {"as_of_date": as_of_date, "live": "true"}
        headers = build_upstream_headers(correlation_id)
        return await self._request(
            operation="report.aggregations.portfolio-snapshot",
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/integration/capabilities"
        params = {"consumer_system": consumer_system, "tenant_id": tenant_id}
        headers = build_upstream_headers(correlation_id)
        return await self._request(
            operation="report.integration.capabilities",
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )

    async def get_report_ordering_catalogue(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/integration/report-ordering-catalogue"
        headers = build_upstream_headers(correlation_id)
        return await self._request(
            operation="report.integration.ordering-catalogue",
            method="GET",
            url=url,
            headers=headers,
        )

    async def post_portfolio_summary(
        self,
        portfolio_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/portfolios/{portfolio_id}/summary"
        headers = build_upstream_headers(correlation_id)
        return await self._request(
            operation="report.portfolio.summary",
            method="POST",
            url=url,
            json_body=payload,
            headers=headers,
        )

    async def post_portfolio_review(
        self,
        portfolio_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/portfolios/{portfolio_id}/review"
        headers = build_upstream_headers(correlation_id)
        return await self._request(
            operation="report.portfolio.review",
            method="POST",
            url=url,
            json_body=payload,
            headers=headers,
        )

    async def submit_portfolio_review_job(
        self,
        *,
        payload: dict[str, Any],
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/portfolio-reviews"
        headers = build_idempotent_upstream_headers(
            correlation_id,
            idempotency_key,
            caller_headers=caller_headers,
        )
        return await self._request(
            operation="report.portfolio-review-jobs.submit",
            method="POST",
            url=url,
            json_body=payload,
            headers=headers,
        )

    async def submit_outcome_review_report_job(
        self,
        *,
        payload: dict[str, Any],
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/outcome-reviews"
        headers = build_idempotent_upstream_headers(
            correlation_id,
            idempotency_key,
            caller_headers=caller_headers,
        )
        return await self._request(
            operation="report.outcome-review-jobs.submit",
            method="POST",
            url=url,
            json_body=payload,
            headers=headers,
        )

    async def get_report_job(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/jobs/{job_id}"
        headers = build_upstream_headers(correlation_id, caller_headers=caller_headers)
        return await self._request(
            operation="report.jobs.get",
            method="GET",
            url=url,
            headers=headers,
        )

    async def list_report_jobs(
        self,
        *,
        filters: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/jobs"
        headers = build_upstream_headers(correlation_id, caller_headers=caller_headers)
        return await self._request(
            operation="report.jobs.list",
            method="GET",
            url=url,
            params=filters,
            headers=headers,
        )

    async def get_report_job_events(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/jobs/{job_id}/events"
        headers = build_upstream_headers(correlation_id, caller_headers=caller_headers)
        return await self._request(
            operation="report.jobs.events",
            method="GET",
            url=url,
            headers=headers,
        )

    async def get_report_job_lineage(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/jobs/{job_id}/lineage"
        headers = build_upstream_headers(correlation_id, caller_headers=caller_headers)
        return await self._request(
            operation="report.jobs.lineage",
            method="GET",
            url=url,
            headers=headers,
        )

    async def get_report_snapshot(
        self,
        *,
        snapshot_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/snapshots/{snapshot_id}"
        headers = build_upstream_headers(correlation_id, caller_headers=caller_headers)
        return await self._request(
            operation="report.snapshots.get",
            method="GET",
            url=url,
            headers=headers,
        )

    async def get_report_snapshot_lineage(
        self,
        *,
        snapshot_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/snapshots/{snapshot_id}/lineage"
        headers = build_upstream_headers(correlation_id, caller_headers=caller_headers)
        return await self._request(
            operation="report.snapshots.lineage",
            method="GET",
            url=url,
            headers=headers,
        )

    async def cancel_report_job(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/jobs/{job_id}/cancel"
        headers = build_upstream_headers(correlation_id, caller_headers=caller_headers)
        return await self._request(
            operation="report.jobs.cancel",
            method="POST",
            url=url,
            headers=headers,
        )

    async def _request(
        self,
        *,
        operation: str,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await request_observed_fanout(
            logger=logger,
            service="lotus-report",
            operation=operation,
            method=method,
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
            json_body=json_body,
        )
