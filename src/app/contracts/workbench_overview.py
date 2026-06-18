from pydantic import BaseModel, Field

from app.contracts.workbench_common import (
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPerformanceSnapshot,
    WorkbenchPortfolioSummary,
    WorkbenchPositionView,
    WorkbenchProjectedPositionView,
    WorkbenchProjectedSummary,
    WorkbenchRebalanceSnapshot,
)


class WorkbenchOverviewResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request boundary.",
        examples=["corr-workbench-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the workbench overview response.",
        examples=["v1"],
    )
    as_of_date: str = Field(
        description="Business as-of date for the workbench snapshot in YYYY-MM-DD format.",
        examples=["2026-02-23"],
    )
    portfolio: WorkbenchPortfolioSummary = Field(
        description="Portfolio identity block for the workbench surface."
    )
    overview: WorkbenchOverviewSummary = Field(
        description="Headline valuation summary for the workbench surface."
    )
    performance_snapshot: WorkbenchPerformanceSnapshot | None = Field(
        default=None,
        description="Optional performance snapshot when lotus-performance is available.",
    )
    rebalance_snapshot: WorkbenchRebalanceSnapshot | None = Field(
        default=None,
        description="Optional rebalance snapshot when lotus-manage is available.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Machine-readable warnings preserved by gateway for the workbench surface.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description="Upstream partial failures preserved for diagnostics and support review.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-workbench-1",
                "contract_version": "v1",
                "as_of_date": "2026-02-23",
                "portfolio": {
                    "portfolio_id": "PF_1001",
                    "client_id": "CIF_1001",
                    "base_currency": "USD",
                    "booking_center_code": "SG",
                },
                "overview": {
                    "market_value_base": 1000.0,
                    "cash_weight_pct": 25.0,
                    "position_count": 3,
                },
                "performance_snapshot": {
                    "period": "YTD",
                    "return_pct": 2.5,
                    "benchmark_return_pct": None,
                },
                "rebalance_snapshot": {
                    "status": "PENDING_REVIEW",
                    "last_rebalance_run_id": "rr_100",
                    "last_run_at_utc": "2026-02-23T01:00:00Z",
                    "supportability": {
                        "feature_key": "manage.observability.action_register_supportability",
                        "state": "healthy",
                        "reason": "action_register_current",
                        "freshness_bucket": "fresh",
                        "run_count": 4,
                        "operation_count": 12,
                        "workflow_decision_count": 3,
                    },
                    "recent_runs": [
                        {
                            "rebalance_run_id": "rr_100",
                            "status": "PENDING_REVIEW",
                            "created_at_utc": "2026-02-23T01:00:00Z",
                            "error_code": None,
                            "workflow_state": "PM_REVIEW_REQUIRED",
                        }
                    ],
                },
                "warnings": [],
                "partial_failures": [],
            }
        }
    }


class WorkbenchPortfolio360Response(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request boundary.",
        examples=["corr-workbench-2"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the portfolio-360 response.",
        examples=["v1"],
    )
    as_of_date: str = Field(
        description="Business as-of date for the portfolio-360 snapshot in YYYY-MM-DD format.",
        examples=["2026-02-23"],
    )
    portfolio: WorkbenchPortfolioSummary = Field(
        description="Portfolio identity block for the portfolio-360 surface."
    )
    overview: WorkbenchOverviewSummary = Field(
        description="Headline valuation summary for the portfolio-360 surface."
    )
    performance_snapshot: WorkbenchPerformanceSnapshot | None = Field(
        default=None,
        description="Optional performance snapshot when lotus-performance is available.",
    )
    rebalance_snapshot: WorkbenchRebalanceSnapshot | None = Field(
        default=None,
        description="Optional rebalance snapshot when lotus-manage is available.",
    )
    current_positions: list[WorkbenchPositionView] = Field(
        default_factory=list,
        description="Current positions published for the baseline portfolio state.",
    )
    projected_positions: list[WorkbenchProjectedPositionView] = Field(
        default_factory=list,
        description="Projected positions published for the active sandbox session when available.",
    )
    projected_summary: WorkbenchProjectedSummary | None = Field(
        default=None,
        description="Projected holdings summary for the active sandbox session when available.",
    )
    active_session_id: str | None = Field(
        default=None,
        description=(
            "Active sandbox session identifier when the portfolio-360 view is session-aware."
        ),
        examples=["sess_1"],
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Machine-readable warnings preserved by gateway for portfolio-360.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description="Upstream partial failures preserved for diagnostics and support review.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-workbench-2",
                "contract_version": "v1",
                "as_of_date": "2026-02-23",
                "portfolio": {
                    "portfolio_id": "PF_1001",
                    "client_id": "CIF_1001",
                    "base_currency": "USD",
                    "booking_center_code": "SG",
                },
                "overview": {
                    "market_value_base": 1000.0,
                    "cash_weight_pct": 25.0,
                    "position_count": 3,
                },
                "performance_snapshot": {
                    "period": "YTD",
                    "return_pct": 2.5,
                    "benchmark_return_pct": None,
                },
                "rebalance_snapshot": {
                    "status": "PENDING_REVIEW",
                    "last_rebalance_run_id": "rr_100",
                    "last_run_at_utc": "2026-02-23T01:00:00Z",
                    "supportability": {
                        "feature_key": "manage.observability.action_register_supportability",
                        "state": "healthy",
                        "reason": "action_register_current",
                        "freshness_bucket": "fresh",
                        "run_count": 4,
                        "operation_count": 12,
                        "workflow_decision_count": 3,
                    },
                    "recent_runs": [
                        {
                            "rebalance_run_id": "rr_100",
                            "status": "PENDING_REVIEW",
                            "created_at_utc": "2026-02-23T01:00:00Z",
                            "error_code": None,
                            "workflow_state": "PM_REVIEW_REQUIRED",
                        }
                    ],
                },
                "current_positions": [
                    {
                        "security_id": "EQ_1",
                        "instrument_name": "Equity 1",
                        "asset_class": "Equity",
                        "quantity": 10.0,
                        "market_value_base": 750.0,
                        "weight_pct": 75.0,
                    }
                ],
                "projected_positions": [
                    {
                        "security_id": "EQ_1",
                        "instrument_name": "Equity 1",
                        "asset_class": "Equity",
                        "baseline_quantity": 10.0,
                        "proposed_quantity": 12.0,
                        "delta_quantity": 2.0,
                    }
                ],
                "projected_summary": {
                    "total_baseline_positions": 1,
                    "total_proposed_positions": 1,
                    "net_delta_quantity": 2.0,
                },
                "active_session_id": "sess_1",
                "warnings": [],
                "partial_failures": [],
            }
        }
    }
