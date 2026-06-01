from app.services.performance_workspace_chart_points import (
    build_workspace_chart_points,
    parse_chart_points,
)


def test_build_workspace_chart_points_maps_active_returns_from_benchmark():
    points = build_workspace_chart_points(
        portfolio_block={
            "breakdowns": {
                "monthly": [
                    {
                        "period": "2026-01",
                        "period_start": "2026-01-01",
                        "period_end": "2026-01-31",
                        "period_return": {"base": 2.34567},
                        "cumulative_return": {"base": 4.56789},
                    }
                ]
            }
        },
        benchmark_block={
            "breakdowns": {
                "monthly": [
                    {
                        "period_return": {"base": 1.11111},
                        "cumulative_return": {"base": 3.22222},
                    }
                ]
            }
        },
        chart_frequency="MONTHLY",
    )

    assert len(points) == 1
    point = points[0]
    assert point.label == "2026-01"
    assert point.frequency == "monthly"
    assert point.period_start == "2026-01-01"
    assert point.period_end == "2026-01-31"
    assert point.portfolio_return_pct == 2.34567
    assert point.benchmark_return_pct == 1.11111
    assert point.active_return_pct == 1.23456
    assert point.cumulative_active_return_pct == 1.34567


def test_build_workspace_chart_points_fails_closed_for_invalid_breakdowns():
    assert (
        build_workspace_chart_points(
            portfolio_block={"breakdowns": []},
            benchmark_block={},
            chart_frequency="monthly",
        )
        == []
    )
    assert (
        build_workspace_chart_points(
            portfolio_block={"breakdowns": {"monthly": {}}},
            benchmark_block={},
            chart_frequency="monthly",
        )
        == []
    )


def test_parse_chart_points_uses_relative_active_returns_when_supplied():
    points = parse_chart_points(
        portfolio_block={
            "breakdowns": {
                "quarterly": [
                    {
                        "period": "2026-Q1",
                        "period_return": {"base": 3.2},
                        "cumulative_return": {"base": 3.2},
                    }
                ]
            }
        },
        benchmark_block={
            "breakdowns": {
                "quarterly": [
                    {
                        "period_return": {"base": 2.5},
                        "cumulative_return": {"base": 2.5},
                    }
                ]
            }
        },
        relative_block={
            "breakdowns": {
                "quarterly": [
                    {
                        "period_return": {"base": 0.7},
                        "cumulative_return": {"base": 0.7},
                    }
                ]
            }
        },
        chart_frequency="QUARTERLY",
    )

    assert len(points) == 1
    point = points[0]
    assert point.label == "2026-Q1"
    assert point.frequency == "quarterly"
    assert point.portfolio_return_pct == 3.2
    assert point.benchmark_return_pct == 2.5
    assert point.active_return_pct == 0.7
    assert point.cumulative_active_return_pct == 0.7


def test_parse_chart_points_tolerates_missing_peer_rows():
    points = parse_chart_points(
        portfolio_block={
            "breakdowns": {
                "monthly": [{"period_return": {"base": 1.0}, "cumulative_return": {"base": 1.0}}]
            }
        },
        benchmark_block={"breakdowns": {"monthly": []}},
        relative_block={"breakdowns": {"monthly": []}},
        chart_frequency="monthly",
    )

    assert len(points) == 1
    assert points[0].label == "point-1"
    assert points[0].benchmark_return_pct is None
    assert points[0].active_return_pct is None
