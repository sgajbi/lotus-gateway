from typing import Any

from app.contracts.portfolio import (
    PortfolioRebalanceSummary,
    PortfolioRebalanceSupportabilitySummary,
)
from app.contracts.portfolio_common import PortfolioPartialFailure

REBALANCE_SUPPORTABILITY_UNAVAILABLE = "PORTFOLIO_REBALANCE_SUPPORTABILITY_UNAVAILABLE"


def parse_workspace_rebalance_summary(
    payload: dict[str, Any],
    supportability: PortfolioRebalanceSupportabilitySummary | None,
) -> PortfolioRebalanceSummary | None:
    items = payload.get("items", [])
    if not isinstance(items, list) or not items:
        return rebalance_summary_from_supportability("NO_RUNS", supportability)
    latest = items[0]
    if not isinstance(latest, dict):
        return rebalance_summary_from_supportability("UNKNOWN", supportability)
    return PortfolioRebalanceSummary(
        status=str(latest.get("status", "UNKNOWN")),
        last_run_at_utc=optional_text(latest.get("created_at")),
        last_rebalance_run_id=optional_text(latest.get("rebalance_run_id")),
        supportability=supportability,
    )


def rebalance_summary_from_supportability(
    status_value: str,
    supportability: PortfolioRebalanceSupportabilitySummary | None,
) -> PortfolioRebalanceSummary | None:
    if supportability is None:
        return None
    return PortfolioRebalanceSummary(
        status=status_value,
        last_run_at_utc=None,
        last_rebalance_run_id=None,
        supportability=supportability,
    )


def parse_workspace_rebalance_supportability(
    payload: dict[str, Any],
    warnings: list[str],
    partial_failures: list[PortfolioPartialFailure],
) -> PortfolioRebalanceSupportabilitySummary | None:
    supportability_payload = payload.get("supportability", payload)
    if not isinstance(supportability_payload, dict):
        warnings.append(REBALANCE_SUPPORTABILITY_UNAVAILABLE)
        partial_failures.append(
            PortfolioPartialFailure(
                source_service="lotus-manage",
                error_code=REBALANCE_SUPPORTABILITY_UNAVAILABLE,
                detail="lotus-manage supportability summary did not include an object payload",
            )
        )
        return None
    return PortfolioRebalanceSupportabilitySummary(
        feature_key=(
            optional_text(supportability_payload.get("feature_key"))
            or "manage.observability.action_register_supportability"
        ),
        state=str(supportability_payload.get("state") or "unknown"),
        reason=optional_text(supportability_payload.get("reason")),
        freshness_bucket=optional_text(supportability_payload.get("freshness_bucket")),
        run_count=optional_int(supportability_payload.get("run_count")),
        operation_count=optional_int(supportability_payload.get("operation_count")),
        workflow_decision_count=optional_int(supportability_payload.get("workflow_decision_count")),
    )


def optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
