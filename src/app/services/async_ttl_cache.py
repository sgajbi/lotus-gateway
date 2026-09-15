import asyncio
from collections.abc import Awaitable, Callable
from copy import copy
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
        self._scope: tuple[object, ...] = ()

    def scoped(self, scope: tuple[object, ...]) -> "AsyncTtlCache[T]":
        """View the existing store through an explicit, immutable ownership namespace."""
        view = copy(self)
        view._scope = (*self._scope, scope)
        return view

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
        key = (*self._scope, *key)
        now = monotonic()
        async with self._lock:
            entry = self._entries.get(key)
            if entry and entry[0] > now:
                return entry[1], True

            task = self._inflight.get(key)
            if task is None:
                task = asyncio.ensure_future(factory())
                if task.done():
                    # An already-completed future must publish before this
                    # call returns: its done-callback would only run on a
                    # later loop turn, leaving a failed future joinable and a
                    # successful one reported as a miss in the meantime.
                    self._record_fill_result(key, task)
                else:
                    task.add_done_callback(partial(self._publish_fill, key))
                    self._inflight[key] = task

        return await asyncio.shield(task), False

    def _publish_fill(self, key: tuple[object, ...], task: asyncio.Future[T]) -> None:
        if self._inflight.get(key) is not task:
            return
        del self._inflight[key]
        self._record_fill_result(key, task)

    def _record_fill_result(self, key: tuple[object, ...], task: asyncio.Future[T]) -> None:
        if task.cancelled() or task.exception() is not None:
            return
        self._entries[key] = (monotonic() + self._ttl_seconds, task.result())

    def clear(self) -> None:
        for entries in (self._entries, self._inflight):
            for key in list(entries):
                if key[: len(self._scope)] == self._scope:
                    del entries[key]

    def discard(self, key: tuple[object, ...]) -> None:
        key = (*self._scope, *key)
        self._entries.pop(key, None)
        self._inflight.pop(key, None)

    def set(self, key: tuple[object, ...], value: T) -> None:
        key = (*self._scope, *key)
        self._inflight.pop(key, None)
        self._entries[key] = (monotonic() + self._ttl_seconds, value)
