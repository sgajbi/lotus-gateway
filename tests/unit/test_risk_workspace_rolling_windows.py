from app.services.risk_workspace_rolling_windows import (
    map_rolling_metric_series,
    map_rolling_window_results,
    rolling_dependency_context,
    rolling_window_lengths,
)


def test_rolling_window_lengths_keeps_numeric_values_as_ints() -> None:
    assert rolling_window_lengths([21, 63.0, "252", None]) == [21, 63]
    assert rolling_window_lengths({"window": 21}) == []


def test_rolling_dependency_context_validates_dict_payloads() -> None:
    context = rolling_dependency_context(
        {
            "requested": True,
            "available": False,
            "aligned": False,
            "reason": "Risk-free series could not be aligned.",
        }
    )

    assert context is not None
    assert context.requested is True
    assert context.available is False
    assert context.aligned is False
    assert context.reason == "Risk-free series could not be aligned."
    assert rolling_dependency_context("not-a-dict") is None


def test_map_rolling_window_results_sorts_windows_and_maps_nested_payloads() -> None:
    windows = map_rolling_window_results(
        [
            "skip-me",
            {
                "window_length": 63,
                "metric_summaries": {
                    "ROLLING_VOLATILITY": {
                        "total_point_count": 66,
                        "computed_point_count": 45,
                        "coverage_ratio": 0.68,
                        "latest": 0.12,
                    },
                    123: {"latest": 0.99},
                    "BROKEN": "skip",
                },
                "metric_series": [
                    {
                        "date": "2026-04-02",
                        "metric_values": {
                            "ROLLING_VOLATILITY": 0.12,
                            "ROLLING_BETA": 0.98,
                            "ROLLING_SHARPE": None,
                            "ROLLING_DRAWDOWN": "n/a",
                        },
                    },
                    "skip-me",
                ],
                "metric_series_context": {
                    "requested": True,
                    "included": True,
                    "emitted_point_count": 1,
                    "reason": "Included for drill-down.",
                },
            },
            {"window_length": 21, "metric_summaries": {}, "metric_series": None},
        ]
    )

    assert [window.window_length for window in windows] == [21, 63]
    assert windows[1].metric_summaries["ROLLING_VOLATILITY"].latest == 0.12
    assert windows[1].metric_series_context is not None
    assert windows[1].metric_series_context.reason == "Included for drill-down."
    assert windows[1].metric_series is not None
    assert windows[1].metric_series[0].metric_values == {
        "ROLLING_VOLATILITY": 0.12,
        "ROLLING_BETA": 0.98,
        "ROLLING_SHARPE": None,
        "ROLLING_DRAWDOWN": None,
    }


def test_map_rolling_metric_series_defaults_missing_metric_values() -> None:
    series = map_rolling_metric_series(
        [
            {"date": "2026-04-01", "metric_values": "not-a-dict"},
            {"date": "2026-04-02"},
            "skip-me",
        ]
    )

    assert [point.date for point in series] == ["2026-04-01", "2026-04-02"]
    assert series[0].metric_values == {}
    assert series[1].metric_values == {}
