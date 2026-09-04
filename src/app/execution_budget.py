from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

RequestResultT = TypeVar("RequestResultT")


class AnalyticsRequestDeadlineExceeded(TimeoutError):
    """Raised when one complete analytics request exhausts its elapsed budget."""


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

    @property
    def is_expired(self) -> bool:
        remaining_seconds = self.remaining_seconds()
        return remaining_seconds is not None and remaining_seconds <= 0

    @property
    def is_bounded(self) -> bool:
        return self.deadline_at is not None

    def request_max_retries(self, default_retries: int) -> int:
        return 0 if self.is_bounded else default_retries

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

    async def run_request(
        self,
        request_factory: Callable[[], Awaitable[RequestResultT]],
    ) -> RequestResultT:
        remaining_seconds = self.remaining_seconds()
        if remaining_seconds is None:
            return await request_factory()
        if remaining_seconds <= 0:
            raise AnalyticsRequestDeadlineExceeded
        try:
            async with asyncio.timeout(remaining_seconds):
                return await request_factory()
        except TimeoutError as exc:
            raise AnalyticsRequestDeadlineExceeded from exc


def _recommended_poll_interval(payload: dict[str, Any], fallback_seconds: float) -> float:
    recommended = payload.get("recommended_poll_after_seconds")
    if isinstance(recommended, bool) or not isinstance(recommended, int | float):
        return fallback_seconds
    resolved = float(recommended)
    if not math.isfinite(resolved) or resolved <= 0:
        return fallback_seconds
    return resolved
