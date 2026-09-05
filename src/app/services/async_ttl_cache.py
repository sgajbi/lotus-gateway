import asyncio
from collections.abc import Awaitable, Callable
from functools import partial
from time import monotonic
from typing import Generic, TypeVar

T = TypeVar("T")


class AsyncTtlCache(Generic[T]):
    """TTL cache that coalesces concurrent fills per key.

    The fill task owns its own completion through a synchronous done-callback:
    waiters await a shielded view, so one waiter's cancellation never cancels
    another waiter's shared work, and a fill that fails or is cancelled
    (including at event-loop shutdown) releases its in-flight slot instead of
    poisoning the key. ``clear``, ``discard`` and ``set`` detach any in-flight
    fill, so a fill started before an invalidation cannot refill the
    invalidated generation or overwrite a newer value; its remaining waiters
    still receive the value their request was admitted against.
    """

    def __init__(self, ttl_seconds: float):
        self._ttl_seconds = ttl_seconds
        self._entries: dict[tuple[object, ...], tuple[float, T]] = {}
        self._inflight: dict[tuple[object, ...], asyncio.Future[T]] = {}
        self._lock = asyncio.Lock()

    async def get_or_set(
        self,
        key: tuple[object, ...],
        factory: Callable[[], Awaitable[T]],
    ) -> T:
        value, _ = await self.get_or_set_with_status(key=key, factory=factory)
        return value

    async def get_or_set_with_status(
        self,
        key: tuple[object, ...],
        factory: Callable[[], Awaitable[T]],
    ) -> tuple[T, bool]:
        now = monotonic()
        async with self._lock:
            entry = self._entries.get(key)
            if entry and entry[0] > now:
                return entry[1], True

            task = self._inflight.get(key)
            if task is None:
                task = asyncio.ensure_future(factory())
                task.add_done_callback(partial(self._publish_fill, key))
                self._inflight[key] = task

        return await asyncio.shield(task), False

    def _publish_fill(self, key: tuple[object, ...], task: asyncio.Future[T]) -> None:
        if self._inflight.get(key) is not task:
            return
        del self._inflight[key]
        if task.cancelled() or task.exception() is not None:
            return
        self._entries[key] = (monotonic() + self._ttl_seconds, task.result())

    def clear(self) -> None:
        self._entries.clear()
        self._inflight.clear()

    def discard(self, key: tuple[object, ...]) -> None:
        self._entries.pop(key, None)
        self._inflight.pop(key, None)

    def set(self, key: tuple[object, ...], value: T) -> None:
        self._inflight.pop(key, None)
        self._entries[key] = (monotonic() + self._ttl_seconds, value)
