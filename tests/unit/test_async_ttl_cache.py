import asyncio
from typing import Any

import pytest

from app.services.async_ttl_cache import AsyncTtlCache


@pytest.mark.asyncio
async def test_async_ttl_cache_reuses_inflight_factory_result() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    started = asyncio.Event()
    release = asyncio.Event()
    call_count = 0

    async def factory() -> int:
        nonlocal call_count
        call_count += 1
        started.set()
        await release.wait()
        return 42

    first_task = asyncio.create_task(cache.get_or_set(("portfolio", "P1"), factory))
    await started.wait()
    second_task = asyncio.create_task(cache.get_or_set(("portfolio", "P1"), factory))
    release.set()

    assert await first_task == 42
    assert await second_task == 42
    assert call_count == 1


@pytest.mark.asyncio
async def test_async_ttl_cache_caches_successful_value_until_cleared() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    call_count = 0

    async def factory() -> int:
        nonlocal call_count
        call_count += 1
        return call_count

    first = await cache.get_or_set(("portfolio", "P1"), factory)
    second = await cache.get_or_set(("portfolio", "P1"), factory)
    cache.clear()
    third = await cache.get_or_set(("portfolio", "P1"), factory)

    assert first == 1
    assert second == 1
    assert third == 2
    assert call_count == 2


@pytest.mark.asyncio
async def test_async_ttl_cache_reports_hit_status() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    calls = 0

    async def factory() -> int:
        nonlocal calls
        calls += 1
        return calls

    first, first_hit = await cache.get_or_set_with_status(("portfolio", "P1"), factory)
    second, second_hit = await cache.get_or_set_with_status(("portfolio", "P1"), factory)

    assert first == 1
    assert second == 1
    assert first_hit is False
    assert second_hit is True
    assert calls == 1


@pytest.mark.asyncio
async def test_async_ttl_cache_retries_after_factory_exception() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    call_count = 0

    async def factory() -> int:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("upstream failed")
        return 7

    with pytest.raises(RuntimeError, match="upstream failed"):
        await cache.get_or_set(("portfolio", "P1"), factory)

    recovered = await cache.get_or_set(("portfolio", "P1"), factory)

    assert recovered == 7
    assert call_count == 2


@pytest.mark.asyncio
async def test_async_ttl_cache_accepts_future_factory_result() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    loop = asyncio.get_running_loop()
    future: asyncio.Future[int] = loop.create_future()

    def factory() -> asyncio.Future[int]:
        return future

    pending = asyncio.create_task(cache.get_or_set(("portfolio", "P1"), factory))
    await asyncio.sleep(0)
    future.set_result(9)

    assert await pending == 9
    assert await cache.get_or_set(("portfolio", "P1"), factory) == 9


@pytest.mark.asyncio
async def test_async_ttl_cache_publishes_an_already_completed_future_synchronously() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    loop = asyncio.get_running_loop()
    calls = 0

    def factory() -> asyncio.Future[int]:
        nonlocal calls
        calls += 1
        future: asyncio.Future[int] = loop.create_future()
        future.set_result(9)
        return future

    value, was_cached = await cache.get_or_set_with_status(("portfolio", "P1"), factory)
    second, second_cached = await cache.get_or_set_with_status(("portfolio", "P1"), factory)

    assert (value, was_cached) == (9, False)
    assert (second, second_cached) == (9, True)
    assert calls == 1


@pytest.mark.asyncio
async def test_async_ttl_cache_recovers_immediately_from_an_already_failed_future() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    loop = asyncio.get_running_loop()
    calls = 0

    def factory() -> asyncio.Future[int]:
        nonlocal calls
        calls += 1
        future: asyncio.Future[int] = loop.create_future()
        if calls == 1:
            future.set_exception(RuntimeError("upstream failed"))
        else:
            future.set_result(7)
        return future

    with pytest.raises(RuntimeError, match="upstream failed"):
        await cache.get_or_set(("portfolio", "P1"), factory)

    recovered = await cache.get_or_set(("portfolio", "P1"), factory)

    assert recovered == 7
    assert calls == 2


@pytest.mark.asyncio
async def test_async_ttl_cache_one_waiter_cancellation_keeps_shared_work_alive() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def factory() -> int:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return 42

    first = asyncio.create_task(cache.get_or_set(("tenant-sg", "P1"), factory))
    await started.wait()
    second = asyncio.create_task(cache.get_or_set(("tenant-sg", "P1"), factory))
    await asyncio.sleep(0)

    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    release.set()

    assert await second == 42
    value, was_cached = await cache.get_or_set_with_status(("tenant-sg", "P1"), factory)
    assert value == 42
    assert was_cached is True
    assert calls == 1


@pytest.mark.asyncio
async def test_async_ttl_cache_cancelled_fill_leaves_key_recoverable() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    started = asyncio.Event()
    release = asyncio.Event()
    fill_tasks: list[asyncio.Task[Any]] = []
    calls = 0

    async def factory() -> int:
        nonlocal calls
        calls += 1
        current = asyncio.current_task()
        assert current is not None
        fill_tasks.append(current)
        started.set()
        await release.wait()
        return calls

    waiter = asyncio.create_task(cache.get_or_set(("tenant-sg", "P1"), factory))
    await started.wait()
    fill_tasks[0].cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter

    release.set()
    recovered = await cache.get_or_set(("tenant-sg", "P1"), factory)

    assert recovered == 2
    assert calls == 2


@pytest.mark.asyncio
async def test_async_ttl_cache_fill_started_before_clear_cannot_refill_the_new_generation() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    first_started = asyncio.Event()
    first_release = asyncio.Event()
    second_started = asyncio.Event()
    second_release = asyncio.Event()
    calls = 0

    async def factory() -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            first_started.set()
            await first_release.wait()
            return 1
        second_started.set()
        await second_release.wait()
        return 2

    stale = asyncio.create_task(cache.get_or_set(("tenant-sg", "P1"), factory))
    await first_started.wait()
    cache.clear()

    fresh = asyncio.create_task(cache.get_or_set(("tenant-sg", "P1"), factory))
    await second_started.wait()

    first_release.set()
    assert await stale == 1
    second_release.set()
    assert await fresh == 2

    value, was_cached = await cache.get_or_set_with_status(("tenant-sg", "P1"), factory)
    assert value == 2
    assert was_cached is True
    assert calls == 2


@pytest.mark.asyncio
async def test_async_ttl_cache_fill_started_before_discard_cannot_overwrite_a_newer_set() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    started = asyncio.Event()
    release = asyncio.Event()

    async def factory() -> int:
        started.set()
        await release.wait()
        return 1

    stale = asyncio.create_task(cache.get_or_set(("tenant-sg", "P1"), factory))
    await started.wait()
    cache.discard(("tenant-sg", "P1"))
    cache.set(("tenant-sg", "P1"), 99)
    release.set()

    assert await stale == 1
    value, was_cached = await cache.get_or_set_with_status(("tenant-sg", "P1"), factory)
    assert value == 99
    assert was_cached is True


@pytest.mark.asyncio
async def test_async_ttl_cache_fill_completion_cannot_overwrite_a_newer_direct_set() -> None:
    cache = AsyncTtlCache[int](ttl_seconds=60)
    started = asyncio.Event()
    release = asyncio.Event()

    async def factory() -> int:
        started.set()
        await release.wait()
        return 1

    stale = asyncio.create_task(cache.get_or_set(("tenant-sg", "P1"), factory))
    await started.wait()
    cache.set(("tenant-sg", "P1"), 99)
    release.set()

    assert await stale == 1
    value, was_cached = await cache.get_or_set_with_status(("tenant-sg", "P1"), factory)
    assert value == 99
    assert was_cached is True
