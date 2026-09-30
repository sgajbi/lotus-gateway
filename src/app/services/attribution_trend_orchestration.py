from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

from app.observability.analytics_ui_metrics import (
    GATEWAY_ATTRIBUTION_TREND_ACTIVE_WINDOWS,
    GATEWAY_ATTRIBUTION_TREND_QUEUED_WINDOWS,
    record_attribution_trend_orchestration,
)

ResultT = TypeVar("ResultT")
AttributionTrendWindowCompletionState = Literal["failed", "timed_out"]


@dataclass(frozen=True)
class AttributionTrendWindowError(Exception):
    """Typed, source-safe final disposition for a trend window without a result."""

    completion_state: AttributionTrendWindowCompletionState
    error_code: str
    detail: str

    def __str__(self) -> str:
        return self.detail


class AttributionTrendAdmissionController:
    """Process-local bulkhead shared by every attribution-trend request."""

    def __init__(self, concurrency_limit: int) -> None:
        if isinstance(concurrency_limit, bool) or not 1 <= concurrency_limit <= 32:
            raise ValueError("Attribution trend concurrency limit must be between 1 and 32")
        self.concurrency_limit = concurrency_limit
        self._semaphore = asyncio.Semaphore(concurrency_limit)

    async def execute(
        self,
        operation: Callable[[], Awaitable[ResultT]],
        *,
        on_admitted: Callable[[], None],
    ) -> ResultT:
        active_metric = GATEWAY_ATTRIBUTION_TREND_ACTIVE_WINDOWS.labels(service="lotus-performance")
        await self._semaphore.acquire()
        try:
            on_admitted()
            active_metric.inc()
            try:
                return await operation()
            finally:
                active_metric.dec()
        finally:
            self._semaphore.release()


class AttributionTrendOrchestrator(Generic[ResultT]):
    """Runs ordered window work through a bounded process bulkhead and elapsed deadline."""

    def __init__(
        self,
        *,
        admission: AttributionTrendAdmissionController,
        deadline_seconds: float,
    ) -> None:
        if not 0 < deadline_seconds <= 120:
            raise ValueError("Attribution trend deadline must be greater than 0 and at most 120s")
        self._admission = admission
        self.deadline_seconds = deadline_seconds

    @property
    def concurrency_limit(self) -> int:
        return self._admission.concurrency_limit

    async def run(
        self,
        *,
        window_count: int,
        operation: Callable[[int], Awaitable[ResultT]],
    ) -> Sequence[ResultT | BaseException]:
        if window_count == 0:
            return ()

        results: list[ResultT | BaseException] = [_deadline_error() for _ in range(window_count)]
        queue: asyncio.Queue[int] = asyncio.Queue()
        for index in range(window_count):
            queue.put_nowait(index)
        started_at = time.perf_counter()
        request_state = "complete"
        queued_metric = GATEWAY_ATTRIBUTION_TREND_QUEUED_WINDOWS.labels(service="lotus-performance")
        queued_count = window_count
        queued_metric.inc(window_count)

        def mark_admitted() -> None:
            nonlocal queued_count
            queued_count -= 1
            queued_metric.dec()

        workers = [
            asyncio.create_task(self._run_worker(queue, results, operation, mark_admitted))
            for _ in range(min(self.concurrency_limit, window_count))
        ]
        try:
            request_state = await self._wait_for_workers(workers)
        except asyncio.CancelledError:
            request_state = "cancelled"
            raise
        finally:
            await _cancel_workers(workers)
            if queued_count:
                queued_metric.dec(queued_count)
            request_state = _resolve_request_state(request_state, results)
            record_attribution_trend_orchestration(
                request_state=request_state,
                duration_seconds=time.perf_counter() - started_at,
            )
        return results

    async def _run_worker(
        self,
        queue: asyncio.Queue[int],
        results: list[ResultT | BaseException],
        operation: Callable[[int], Awaitable[ResultT]],
        mark_admitted: Callable[[], None],
    ) -> None:
        while True:
            try:
                index = queue.get_nowait()
            except asyncio.QueueEmpty:
                return

            async def admitted_operation() -> ResultT:
                return await operation(index)

            try:
                results[index] = await self._admission.execute(
                    admitted_operation,
                    on_admitted=mark_admitted,
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                results[index] = exc

    async def _wait_for_workers(self, workers: list[asyncio.Task[None]]) -> str:
        try:
            await asyncio.wait_for(
                asyncio.gather(*workers),
                timeout=self.deadline_seconds,
            )
        except TimeoutError:
            return "timed_out"
        return "complete"


def _deadline_error() -> AttributionTrendWindowError:
    return AttributionTrendWindowError(
        completion_state="timed_out",
        error_code="ATTRIBUTION_TREND_DEADLINE_EXCEEDED",
        detail="Attribution trend window exceeded the Gateway elapsed deadline.",
    )


async def _cancel_workers(workers: Sequence[asyncio.Task[None]]) -> None:
    for worker_task in workers:
        if not worker_task.done():
            worker_task.cancel()
    await asyncio.gather(*workers, return_exceptions=True)


def _resolve_request_state(request_state: str, results: Sequence[object]) -> str:
    if request_state != "complete":
        return request_state
    has_failure = any(
        isinstance(result, BaseException)
        or (
            isinstance(result, tuple) and result and isinstance(result[0], int) and result[0] >= 400
        )
        for result in results
    )
    return "partial" if has_failure else "complete"
