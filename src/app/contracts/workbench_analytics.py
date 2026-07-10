from pydantic import BaseModel, Field

from app.contracts.workbench_common import WorkbenchPartialFailure


class WorkbenchAnalyticsBucket(BaseModel):
    bucket_key: str = Field(
        description="Stable grouping key for the analytics bucket.",
        examples=["EQUITY"],
    )
    bucket_label: str = Field(
        description="Advisor-facing grouping label for the analytics bucket.",
        examples=["EQUITY"],
    )
    current_quantity: float = Field(
        description="Current quantity represented by the analytics bucket.",
        examples=[10.0],
    )
    proposed_quantity: float = Field(
        description="Projected quantity represented by the analytics bucket.",
        examples=[12.0],
    )
    delta_quantity: float = Field(
        description="Delta quantity between current and projected bucket states.",
        examples=[2.0],
    )
    current_weight_pct: float = Field(
        description="Current bucket weight in percentage points.",
        examples=[100.0],
    )
    proposed_weight_pct: float = Field(
        description="Projected bucket weight in percentage points.",
        examples=[100.0],
    )


class WorkbenchTopChange(BaseModel):
    security_id: str = Field(
        description="Stable security identifier for the top change row.",
        examples=["EQ_1"],
    )
    instrument_name: str = Field(
        description="Advisor-facing instrument label for the top change row.",
        examples=["Equity 1"],
    )
    delta_quantity: float = Field(
        description="Quantity delta contributed by the change row.",
        examples=[2.0],
    )
    direction: str = Field(
        description="Direction of the top change such as INCREASE or DECREASE.",
        examples=["INCREASE"],
    )


class WorkbenchAnalyticsResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request boundary.",
        examples=["corr-workbench-3"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the workbench analytics response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Canonical portfolio identifier for the analytics response.",
        examples=["PF_1001"],
    )
    session_id: str | None = Field(
        default=None,
        description="Active sandbox session identifier when analytics include a projected state.",
        examples=["sess_1"],
    )
    period: str = Field(
        description="Analytics horizon requested by the caller.",
        examples=["YTD"],
    )
    group_by: str = Field(
        description="Grouping dimension requested for allocation and change analytics.",
        examples=["ASSET_CLASS"],
    )
    benchmark_code: str = Field(
        description="Benchmark code resolved for the analytics response.",
        examples=["MODEL_60_40"],
    )
    portfolio_return_pct: float | None = Field(
        default=None,
        description="Portfolio return for the requested analytics horizon in percentage points.",
        examples=[1.5],
    )
    benchmark_return_pct: float | None = Field(
        default=None,
        description="Benchmark return for the requested analytics horizon in percentage points.",
        examples=[3.1],
    )
    active_return_pct: float | None = Field(
        default=None,
        description="Active return versus benchmark in percentage points.",
        examples=[-1.6],
    )
    allocation_buckets: list[WorkbenchAnalyticsBucket] = Field(
        default_factory=list,
        description="Grouped allocation bucket deltas for the analytics response.",
    )
    top_changes: list[WorkbenchTopChange] = Field(
        default_factory=list,
        description="Largest projected position changes for the analytics response.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Machine-readable warnings preserved by gateway for analytics.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description="Upstream partial failures preserved for analytics diagnostics.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-workbench-3",
                "contract_version": "v1",
                "portfolio_id": "PF_1001",
                "session_id": "sess_1",
                "period": "YTD",
                "group_by": "ASSET_CLASS",
                "benchmark_code": "MODEL_60_40",
                "portfolio_return_pct": 1.5,
                "benchmark_return_pct": None,
                "active_return_pct": None,
                "allocation_buckets": [
                    {
                        "bucket_key": "EQUITY",
                        "bucket_label": "EQUITY",
                        "current_quantity": 10.0,
                        "proposed_quantity": 12.0,
                        "delta_quantity": 2.0,
                        "current_weight_pct": 100.0,
                        "proposed_weight_pct": 100.0,
                    }
                ],
                "top_changes": [
                    {
                        "security_id": "EQ_1",
                        "instrument_name": "Equity 1",
                        "delta_quantity": 2.0,
                        "direction": "INCREASE",
                    }
                ],
                "warnings": ["RISK_BFF_PENDING"],
                "partial_failures": [
                    {
                        "source_service": "lotus-risk",
                        "error_code": "RISK_BFF_NOT_IMPLEMENTED",
                        "detail": (
                            "Legacy workbench risk proxy was removed. Stateful concentration "
                            "risk will be restored through the RFC-0022 Gateway Risk BFF."
                        ),
                    }
                ],
            }
        }
    }
