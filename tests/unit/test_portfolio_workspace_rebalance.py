from app.contracts.portfolio import PortfolioPartialFailure
from app.services.portfolio_workspace_rebalance import (
    parse_workspace_rebalance_summary,
    parse_workspace_rebalance_supportability,
    rebalance_summary_from_supportability,
)


def test_parse_workspace_rebalance_summary_uses_latest_run() -> None:
    supportability = parse_workspace_rebalance_supportability(
        {
            "supportability": {
                "feature_key": "manage.observability.action_register_supportability",
                "state": "ready",
                "run_count": "3",
                "operation_count": 12,
                "workflow_decision_count": "5",
            }
        },
        [],
        [],
    )

    summary = parse_workspace_rebalance_summary(
        {
            "items": [
                {
                    "status": "APPROVED",
                    "created_at": "2026-06-12T10:15:00Z",
                    "rebalance_run_id": "run-123",
                }
            ]
        },
        supportability,
    )

    assert summary is not None
    assert summary.status == "APPROVED"
    assert summary.last_run_at_utc == "2026-06-12T10:15:00Z"
    assert summary.last_rebalance_run_id == "run-123"
    assert summary.supportability is supportability
    assert summary.supportability is not None
    assert summary.supportability.run_count == 3
    assert summary.supportability.operation_count == 12
    assert summary.supportability.workflow_decision_count == 5


def test_parse_workspace_rebalance_summary_uses_no_runs_when_items_empty() -> None:
    supportability = parse_workspace_rebalance_supportability({"state": "degraded"}, [], [])

    summary = parse_workspace_rebalance_summary({"items": []}, supportability)

    assert summary is not None
    assert summary.status == "NO_RUNS"
    assert summary.last_run_at_utc is None
    assert summary.last_rebalance_run_id is None
    assert summary.supportability is supportability


def test_parse_workspace_rebalance_summary_uses_unknown_when_latest_is_malformed() -> None:
    supportability = parse_workspace_rebalance_supportability({"state": "ready"}, [], [])

    summary = parse_workspace_rebalance_summary({"items": ["not-a-run"]}, supportability)

    assert summary is not None
    assert summary.status == "UNKNOWN"
    assert summary.supportability is supportability


def test_rebalance_summary_from_supportability_requires_supportability() -> None:
    assert rebalance_summary_from_supportability("NO_RUNS", None) is None


def test_parse_workspace_rebalance_supportability_records_invalid_payload() -> None:
    warnings: list[str] = []
    partial_failures: list[PortfolioPartialFailure] = []

    supportability = parse_workspace_rebalance_supportability(
        {"supportability": []},
        warnings,
        partial_failures,
    )

    assert supportability is None
    assert warnings == ["PORTFOLIO_REBALANCE_SUPPORTABILITY_UNAVAILABLE"]
    assert len(partial_failures) == 1
    assert partial_failures[0].source_service == "lotus-manage"
    assert partial_failures[0].error_code == "PORTFOLIO_REBALANCE_SUPPORTABILITY_UNAVAILABLE"


def test_parse_workspace_rebalance_supportability_defaults_and_invalid_counts() -> None:
    supportability = parse_workspace_rebalance_supportability(
        {
            "state": None,
            "reason": "source_unavailable",
            "freshness_bucket": "stale",
            "run_count": "not-an-int",
            "operation_count": None,
            "workflow_decision_count": "7",
        },
        [],
        [],
    )

    assert supportability is not None
    assert supportability.feature_key == "manage.observability.action_register_supportability"
    assert supportability.state == "unknown"
    assert supportability.reason == "source_unavailable"
    assert supportability.freshness_bucket == "stale"
    assert supportability.run_count is None
    assert supportability.operation_count is None
    assert supportability.workflow_decision_count == 7
