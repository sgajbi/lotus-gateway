from __future__ import annotations

import asyncio
import logging
import math
import time
from dataclasses import dataclass
from typing import Any

from app.clients.http_resilience import request_with_retry
from app.clients.upstream_headers import build_upstream_headers
from app.observability.analytics_ui import (
    emit_gateway_analytics_fanout_log,
    gateway_analytics_fanout_timer,
)

logger = logging.getLogger("analytics_ui.gateway")


@dataclass(frozen=True)
class AnalyticsPollBudget:
    """Elapsed-time policy for one analytics submission and its result reads."""

    deadline_at: float | None

    @classmethod
    def from_timeout(cls, timeout_seconds: float | None) -> AnalyticsPollBudget:
        deadline_at = None if timeout_seconds is None else time.monotonic() + timeout_seconds
        return cls(deadline_at=deadline_at)

    @classmethod
    def unbounded(cls) -> AnalyticsPollBudget:
        return cls(deadline_at=None)

    def remaining_seconds(self) -> float | None:
        if self.deadline_at is None:
            return None
        return self.deadline_at - time.monotonic()

    def request_timeout(self, default_seconds: float) -> float:
        remaining_seconds = self.remaining_seconds()
        if remaining_seconds is None:
            return default_seconds
        return min(default_seconds, max(remaining_seconds, 0.001))

    def poll_interval(self, *, payload: dict[str, Any], fallback_seconds: float) -> float:
        interval_seconds = _recommended_poll_interval(payload, fallback_seconds)
        remaining_seconds = self.remaining_seconds()
        if remaining_seconds is None:
            return interval_seconds
        return min(interval_seconds, max(remaining_seconds, 0.0))


def build_async_poll_deadline_payload(
    *, result_path: str, accepted_payload: dict[str, Any] | None
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "detail": "analytics result did not complete within the governed Gateway deadline",
        "error_code": "ASYNC_RESULT_DEADLINE_EXHAUSTED",
        "state": "degraded",
        "reason": "async_poll_deadline_exhausted",
        "result_path": result_path,
    }
    calculation_id = (accepted_payload or {}).get("calculation_id")
    if isinstance(calculation_id, str) and calculation_id:
        payload["calculation_id"] = calculation_id
    return payload


def _recommended_poll_interval(payload: dict[str, Any], fallback_seconds: float) -> float:
    recommended = payload.get("recommended_poll_after_seconds")
    if isinstance(recommended, bool) or not isinstance(recommended, int | float):
        return fallback_seconds
    resolved = float(recommended)
    if not math.isfinite(resolved) or resolved <= 0:
        return fallback_seconds
    return resolved


@dataclass(frozen=True)
class _AnalyticsPollContext:
    result_path: str
    url: str
    headers: dict[str, str]
    service: str
    operation: str
    budget: AnalyticsPollBudget
    accepted_payload: dict[str, Any] | None
    started_at: float


@dataclass
class _AnalyticsPollState:
    attempts: int
    status_code: int
    payload: dict[str, Any]


class LotusAnalyticsAsyncPollingMixin:
    _base_url: str
    _timeout: float
    _retry_backoff_seconds: float

    @staticmethod
    def _emit_analytics_read_audit(*, operation: str, status_code: int) -> None:
        raise NotImplementedError

    async def _poll_async_result(
        self,
        *,
        result_path: str,
        correlation_id: str,
        service: str,
        operation: str,
        max_attempts: int | None = 10,
        poll_interval_seconds: float = 0.35,
        poll_budget: AnalyticsPollBudget | None = None,
        accepted_payload: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        context = self._build_poll_context(
            result_path=result_path,
            correlation_id=correlation_id,
            service=service,
            operation=operation,
            poll_budget=poll_budget,
            accepted_payload=accepted_payload,
        )
        return await self._run_async_poll_loop(
            context=context,
            max_attempts=max_attempts,
            poll_interval_seconds=poll_interval_seconds,
        )

    def _build_poll_context(
        self,
        *,
        result_path: str,
        correlation_id: str,
        service: str,
        operation: str,
        poll_budget: AnalyticsPollBudget | None,
        accepted_payload: dict[str, Any] | None,
    ) -> _AnalyticsPollContext:
        return _AnalyticsPollContext(
            result_path=result_path,
            url=self._async_result_url(result_path),
            headers=build_upstream_headers(correlation_id),
            service=service,
            operation=operation,
            budget=poll_budget or AnalyticsPollBudget.unbounded(),
            accepted_payload=accepted_payload,
            started_at=gateway_analytics_fanout_timer(),
        )

    async def _run_async_poll_loop(
        self,
        *,
        context: _AnalyticsPollContext,
        max_attempts: int | None,
        poll_interval_seconds: float,
    ) -> tuple[int, dict[str, Any]]:
        state = _AnalyticsPollState(
            attempts=0,
            status_code=202,
            payload=context.accepted_payload or {"detail": "async analytics result still pending"},
        )
        while max_attempts is None or state.attempts < max_attempts:
            deadline_result = self._expired_poll_deadline_result(context)
            if deadline_result is not None:
                return deadline_result
            state.status_code, state.payload = await self._poll_analytics_result_once(
                context=context
            )
            state.attempts += 1
            if state.status_code != 202:
                self._emit_analytics_read_audit(
                    operation=f"{context.operation}.poll",
                    status_code=state.status_code,
                )
                return state.status_code, state.payload
            deadline_result = await self._wait_for_next_async_poll(
                context=context,
                payload=state.payload,
                fallback_seconds=poll_interval_seconds,
            )
            if deadline_result is not None:
                return deadline_result
        return state.status_code, state.payload

    def _expired_poll_deadline_result(
        self, context: _AnalyticsPollContext
    ) -> tuple[int, dict[str, Any]] | None:
        remaining_seconds = context.budget.remaining_seconds()
        if remaining_seconds is None or remaining_seconds > 0:
            return None
        return self._async_poll_deadline_result(context)

    async def _wait_for_next_async_poll(
        self,
        *,
        context: _AnalyticsPollContext,
        payload: dict[str, Any],
        fallback_seconds: float,
    ) -> tuple[int, dict[str, Any]] | None:
        sleep_seconds = context.budget.poll_interval(
            payload=payload,
            fallback_seconds=fallback_seconds,
        )
        if sleep_seconds > 0:
            await asyncio.sleep(sleep_seconds)
            return None
        return self._async_poll_deadline_result(context)

    def _async_result_url(self, result_path: str) -> str:
        if result_path.startswith("http://") or result_path.startswith("https://"):
            return result_path
        return f"{self._base_url}{result_path}"

    async def _poll_analytics_result_once(
        self, *, context: _AnalyticsPollContext
    ) -> tuple[int, dict[str, Any]]:
        started_at = gateway_analytics_fanout_timer()
        status_code, payload = await request_with_retry(
            method="GET",
            url=context.url,
            timeout_seconds=context.budget.request_timeout(self._timeout),
            max_retries=0,
            backoff_seconds=self._retry_backoff_seconds,
            headers=context.headers,
            retry_timeout_exceptions=False,
        )
        emit_gateway_analytics_fanout_log(
            logger=logger,
            started_at=started_at,
            service=context.service,
            operation=f"{context.operation}.poll",
            status_code=status_code,
            payload=payload,
        )
        return status_code, payload

    @staticmethod
    def _async_poll_deadline_result(
        context: _AnalyticsPollContext,
    ) -> tuple[int, dict[str, Any]]:
        payload = build_async_poll_deadline_payload(
            result_path=context.result_path,
            accepted_payload=context.accepted_payload,
        )
        emit_gateway_analytics_fanout_log(
            logger=logger,
            started_at=context.started_at,
            service=context.service,
            operation=f"{context.operation}.poll",
            status_code=504,
            payload=payload,
        )
        return 504, payload
