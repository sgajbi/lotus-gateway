from app.contracts import portfolio
from app.contracts.portfolio_common import PortfolioPartialFailure
from app.contracts.portfolio_performance_snapshot import (
    PortfolioPerformanceSnapshotPoint,
    PortfolioPerformanceSnapshotResponse,
    PortfolioPerformanceSnapshotUnavailable,
)


def test_portfolio_performance_snapshot_contracts_remain_reexported() -> None:
    assert portfolio.PortfolioPartialFailure is PortfolioPartialFailure
    assert portfolio.PortfolioPerformanceSnapshotPoint is PortfolioPerformanceSnapshotPoint
    assert portfolio.PortfolioPerformanceSnapshotResponse is (PortfolioPerformanceSnapshotResponse)
    assert portfolio.PortfolioPerformanceSnapshotUnavailable is (
        PortfolioPerformanceSnapshotUnavailable
    )
