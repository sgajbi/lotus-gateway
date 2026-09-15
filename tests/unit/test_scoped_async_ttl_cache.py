import asyncio

import pytest

from app.services.async_ttl_cache import AsyncTtlCache


@pytest.mark.asyncio
async def test_scoped_views_share_only_equal_authority_and_preserve_late_fill_fences():
    store = AsyncTtlCache[str](60)
    a = store.scoped(("tenant-a", "advisor"))
    b = store.scoped(("tenant-b", "advisor"))
    other_actor = store.scoped(("tenant-a", "other-advisor"))
    started, release = asyncio.Event(), asyncio.Event()

    async def old_result():
        started.set()
        await release.wait()
        return "old-a"

    async def unexpected_read():
        pytest.fail("same admitted scope must reuse its result")

    old = asyncio.create_task(a.get_or_set(("same-portfolio",), old_result))
    await started.wait()
    b.set(("same-portfolio",), "result-b")
    other_actor.set(("same-portfolio",), "other-actor")
    a.clear()
    a.set(("same-portfolio",), "new-a")
    release.set()
    assert await old == "old-a"
    assert await a.get_or_set(("same-portfolio",), unexpected_read) == "new-a"
    assert await b.get_or_set(("same-portfolio",), unexpected_read) == "result-b"
    assert await other_actor.get_or_set(("same-portfolio",), unexpected_read) == "other-actor"
    repeated = store.scoped(("tenant-a", "advisor"))
    assert await repeated.get_or_set(("same-portfolio",), unexpected_read) == "new-a"
    repeated.discard(("same-portfolio",))

    async def restored():
        return "restored-a"

    assert await a.get_or_set(("same-portfolio",), restored) == "restored-a"
    store.clear()
    assert await b.get_or_set(("same-portfolio",), restored) == "restored-a"
