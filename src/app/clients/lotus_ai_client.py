from __future__ import annotations

from typing import Any

from app.clients.http_resilience import request_with_retry
from app.middleware.correlation import propagation_headers


class LotusAiClient:
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

    async def execute_task(
        self,
        *,
        task_id: str,
        caller_app: str,
        correlation_id: str,
        context_summary: str,
        context_payload: dict[str, Any],
        source_refs: list[str],
        expected_output_label: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        request_payload: dict[str, Any] = {
            "task_id": task_id,
            "input_mode": "STRUCTURED_CONTEXT",
            "caller": {
                "caller_app": caller_app,
                "correlation_id": correlation_id,
            },
            "context": {
                "summary": context_summary,
                "payload": context_payload,
                "source_refs": source_refs,
            },
        }
        if expected_output_label:
            request_payload["expected_output_label"] = expected_output_label

        return await request_with_retry(
            method="POST",
            url=f"{self._base_url}/ai/tasks/execute",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=request_payload,
            headers=propagation_headers(correlation_id),
            retry_timeout_exceptions=False,
        )

    async def execute_workflow_pack(
        self,
        *,
        pack_id: str,
        version: str,
        environment: str,
        caller_identity_class: str,
        workflow_surface: str | None,
        task_request: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await request_with_retry(
            method="POST",
            url=f"{self._base_url}/platform/workflow-packs/execute",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body={
                "pack_id": pack_id,
                "version": version,
                "environment": environment,
                "caller_identity_class": caller_identity_class,
                "workflow_surface": workflow_surface,
                "task_request": task_request,
            },
            headers=propagation_headers(correlation_id),
            retry_timeout_exceptions=False,
        )

    async def get_workflow_pack_run_consumer_view(
        self,
        *,
        run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await request_with_retry(
            method="GET",
            url=f"{self._base_url}/platform/workflow-packs/runs/{run_id}/consumer-view",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=propagation_headers(correlation_id),
            retry_timeout_exceptions=False,
        )

    async def get_workflow_pack_run_operator_profile(
        self,
        *,
        run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await request_with_retry(
            method="GET",
            url=f"{self._base_url}/platform/workflow-packs/runs/{run_id}/operator-profile",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=propagation_headers(correlation_id),
            retry_timeout_exceptions=False,
        )

    async def list_workflow_pack_task_flows(
        self,
        *,
        correlation_id: str,
        workflow_pack_id: str | None = None,
        caller: str | None = None,
        workflow_surface: str | None = None,
        limit: int = 25,
    ) -> tuple[int, dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if workflow_pack_id is not None:
            params["workflow_pack_id"] = workflow_pack_id
        if caller is not None:
            params["caller"] = caller
        if workflow_surface is not None:
            params["workflow_surface"] = workflow_surface
        return await request_with_retry(
            method="GET",
            url=f"{self._base_url}/platform/workflow-packs/task-flows",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=propagation_headers(correlation_id),
            retry_timeout_exceptions=False,
        )

    async def apply_workflow_pack_run_review_action(
        self,
        *,
        run_id: str,
        correlation_id: str,
        request_payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        return await request_with_retry(
            method="POST",
            url=f"{self._base_url}/platform/workflow-packs/runs/{run_id}/review-actions",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=request_payload,
            headers=propagation_headers(correlation_id),
            retry_timeout_exceptions=False,
        )
