"""Caches of Core-fenced results are partitioned by the admitted tenant: one
tenant's cached response must never satisfy another tenant's read."""

import pytest

from app.middleware.caller_identity import (
    capture_caller_identity,
    release_caller_identity,
)
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_benchmarks import benchmark_catalog_cache_key
from app.services.portfolio_upstream_access import PortfolioUpstreamAccessMixin


def _under_tenant(tenant: str):
    return capture_caller_identity({"X-Tenant-Id": tenant})


def test_benchmark_catalog_cache_key_is_partitioned_by_admitted_tenant() -> None:
    token = _under_tenant("tenant-a")
    try:
        key_a = benchmark_catalog_cache_key(report_end_date="2026-04-10", reporting_currency="USD")
    finally:
        release_caller_identity(token)
    token = _under_tenant("tenant-b")
    try:
        key_b = benchmark_catalog_cache_key(report_end_date="2026-04-10", reporting_currency="USD")
    finally:
        release_caller_identity(token)

    assert key_a != key_b
    assert "tenant-a" in key_a
    assert "tenant-b" in key_b


class _CachedAccess(PortfolioUpstreamAccessMixin):
    def __init__(self) -> None:
        self._upstream_cache = AsyncTtlCache(ttl_seconds=60)


@pytest.mark.asyncio
async def test_portfolio_upstream_cache_never_serves_across_tenants() -> None:
    access = _CachedAccess()
    calls: list[str] = []

    def loader_for(tenant: str):
        async def _loader():
            calls.append(tenant)
            return 200, {"tenant": tenant}

        return _loader

    token = _under_tenant("tenant-a")
    try:
        first = await access._get_cached_upstream_result(
            ("portfolio", "PB_001"), loader_for("tenant-a")
        )
        repeat = await access._get_cached_upstream_result(
            ("portfolio", "PB_001"), loader_for("tenant-a")
        )
    finally:
        release_caller_identity(token)
    token = _under_tenant("tenant-b")
    try:
        second = await access._get_cached_upstream_result(
            ("portfolio", "PB_001"), loader_for("tenant-b")
        )
    finally:
        release_caller_identity(token)

    assert first == (200, {"tenant": "tenant-a"})
    assert repeat == (200, {"tenant": "tenant-a"})
    assert second == (200, {"tenant": "tenant-b"})
    # Same tenant reuses the cached entry; a different tenant always loads.
    assert calls == ["tenant-a", "tenant-b"]
