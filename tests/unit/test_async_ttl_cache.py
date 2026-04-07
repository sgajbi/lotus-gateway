import asyncio

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
