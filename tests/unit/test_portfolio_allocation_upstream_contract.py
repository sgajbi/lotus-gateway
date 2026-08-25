from typing import Any

import pytest

from app.clients.lotus_core_portfolio_query_client import LotusCorePortfolioQueryClientMixin


class _AllocationClient(LotusCorePortfolioQueryClientMixin):
    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None

    async def _post_query_resource(self, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        self.payload = kwargs["payload"]
        return 200, {"views": []}


@pytest.mark.asyncio
async def test_query_asset_allocation_forwards_bounded_contributor_limit() -> None:
    client = _AllocationClient()

    await client.query_asset_allocation(
        correlation_id="corr-allocation",
        portfolio_id="PF_1001",
        dimensions=["asset_class", "region"],
        as_of_date="2026-03-27",
        reporting_currency="USD",
        look_through_mode="prefer_look_through",
        contributor_limit_per_bucket=25,
    )

    assert client.payload == {
        "scope": {"portfolio_id": "PF_1001"},
        "dimensions": ["asset_class", "region"],
        "as_of_date": "2026-03-27",
        "reporting_currency": "USD",
        "look_through_mode": "prefer_look_through",
        "contributor_limit_per_bucket": 25,
    }
