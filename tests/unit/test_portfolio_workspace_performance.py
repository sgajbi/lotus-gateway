from app.services.portfolio_workspace_performance import parse_workspace_performance_summary


def test_parse_workspace_performance_summary_prefers_ytd_period() -> None:
    warnings: list[str] = []

    summary = parse_workspace_performance_summary(
        {
            "results_by_period": {
                "1Y": {
                    "portfolio": {
                        "summary": {"period_return": {"base": "0.10123"}},
                    }
                },
                "YTD": {
                    "portfolio": {
                        "summary": {"period_return": {"base": "0.05123"}},
                    }
                },
            }
        },
        warnings,
    )

    assert summary is not None
    assert summary.period == "YTD"
    assert summary.return_pct == 0.05123
    assert warnings == []


def test_parse_workspace_performance_summary_falls_back_to_first_period() -> None:
    warnings: list[str] = []

    summary = parse_workspace_performance_summary(
        {
            "resultsByPeriod": {
                "1Y": {
                    "portfolio": {
                        "summary": {"period_return": {"base": "0.10123"}},
                    }
                }
            }
        },
        warnings,
    )

    assert summary is not None
    assert summary.period == "1Y"
    assert summary.return_pct == 0.10123
    assert warnings == []


def test_parse_workspace_performance_summary_records_invalid_period_container() -> None:
    warnings: list[str] = []

    summary = parse_workspace_performance_summary({"results_by_period": []}, warnings)

    assert summary is None
    assert warnings == ["PORTFOLIO_PERFORMANCE_INVALID"]


def test_parse_workspace_performance_summary_ignores_malformed_period_payload() -> None:
    warnings: list[str] = []

    summary = parse_workspace_performance_summary({"results_by_period": {"YTD": []}}, warnings)

    assert summary is None
    assert warnings == []


def test_parse_workspace_performance_summary_preserves_invalid_return_as_none() -> None:
    warnings: list[str] = []

    summary = parse_workspace_performance_summary(
        {
            "results_by_period": {
                "YTD": {
                    "portfolio": {
                        "summary": {"period_return": {"base": "not-a-number"}},
                    }
                }
            }
        },
        warnings,
    )

    assert summary is not None
    assert summary.period == "YTD"
    assert summary.return_pct is None
    assert warnings == []
