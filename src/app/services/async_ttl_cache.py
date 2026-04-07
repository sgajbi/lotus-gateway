import asyncio
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Coroutine, Generic, TypeVar, cast

T = TypeVar("T")


class AsyncTtlCache(Generic[T]):
    def __init__(self, ttl_seconds: float):
        self._ttl_seconds = ttl_seconds
        self._entries: dict[tuple[object, ...], tuple[float, T]] = {}
        self._inflight: dict[tuple[object, ...], asyncio.Task[T]] = {}
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
                task = asyncio.create_task(cast(Coroutine[object, object, T], factory()))
                self._inflight[key] = task

        try:
            value = await task
        except Exception:
            async with self._lock:
                current = self._inflight.get(key)
                if current is task:
                    self._inflight.pop(key, None)
            raise

        async with self._lock:
            self._entries[key] = (monotonic() + self._ttl_seconds, value)
            current = self._inflight.get(key)
            if current is task:
                self._inflight.pop(key, None)
        return value, False

    def clear(self) -> None:
        self._entries.clear()
        self._inflight.clear()
