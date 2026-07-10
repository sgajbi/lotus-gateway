from pydantic import BaseModel, Field

from app.contracts.workbench_common import (
    WorkbenchPartialFailure,
    WorkbenchProjectedPositionView,
    WorkbenchProjectedSummary,
)


class WorkbenchSandboxSessionCreateRequest(BaseModel):
    created_by: str | None = Field(
        default=None,
        description="Optional user or system identifier that created the sandbox session.",
        examples=["advisor_1"],
    )
    ttl_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Requested sandbox session lifetime in hours before expiry.",
        examples=[24],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "created_by": "advisor_1",
                "ttl_hours": 24,
            }
        }
    }


class WorkbenchSandboxChangeInput(BaseModel):
    security_id: str = Field(
        description="Stable security identifier targeted by the sandbox change.",
        examples=["EQ_1"],
    )
    transaction_type: str = Field(
        description="Transaction intent applied in the sandbox, such as BUY or SELL.",
        examples=["BUY"],
    )
    quantity: float | None = Field(
        default=None,
        description="Proposed transaction quantity when the sandbox change is quantity-based.",
        examples=[2.0],
    )
    price: float | None = Field(
        default=None,
        description="Optional unit price used to value the sandbox change.",
        examples=[101.25],
    )
    amount: float | None = Field(
        default=None,
        description="Optional monetary amount used when the sandbox change is amount-based.",
        examples=[5000.0],
    )
    currency: str | None = Field(
        default=None,
        description="Optional transaction currency for the sandbox change.",
        examples=["USD"],
    )
    effective_date: str | None = Field(
        default=None,
        description="Optional effective date for the sandbox change in YYYY-MM-DD format.",
        examples=["2026-02-24"],
    )
    metadata: dict[str, str | int | float | bool] | None = Field(
        default=None,
        description="Optional strategy or workflow metadata preserved with the sandbox change.",
        examples=[{"ticket_id": "SIM-101", "rebalance": True}],
    )


class WorkbenchSandboxApplyChangesRequest(BaseModel):
    changes: list[WorkbenchSandboxChangeInput] = Field(
        default_factory=list,
        description="Ordered sandbox changes applied to the active simulation session.",
    )
    evaluate_policy: bool = Field(
        default=False,
        description="Whether gateway should request policy evaluation after applying the changes.",
        examples=[True],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "changes": [
                    {
                        "security_id": "EQ_1",
                        "transaction_type": "BUY",
                        "quantity": 2.0,
                        "price": 101.25,
                        "currency": "USD",
                        "effective_date": "2026-02-24",
                        "metadata": {"ticket_id": "SIM-101", "rebalance": True},
                    }
                ],
                "evaluate_policy": True,
            }
        }
    }


class WorkbenchPolicyFeedback(BaseModel):
    status: str = Field(
        description="Policy gate outcome returned for the sandbox projection.",
        examples=["PASS"],
    )
    detail: str | None = Field(
        default=None,
        description="Optional human-readable explanation of the policy gate outcome.",
        examples=["Simulation passed portfolio policy checks."],
    )
    raw: dict | None = Field(
        default=None,
        description="Optional raw policy payload preserved for diagnostics and audit review.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "PASS",
                "detail": "Simulation passed portfolio policy checks.",
                "raw": {
                    "status": "COMPLETED",
                    "gate_decision": {"status": "PASS", "reason_code": "ALL_CHECKS_PASSED"},
                },
            }
        }
    }


class WorkbenchSandboxStateResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request boundary.",
        examples=["corr-workbench-sandbox-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the workbench sandbox response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Canonical portfolio identifier for the sandbox projection.",
        examples=["PF_1001"],
    )
    session_id: str = Field(
        description="Active simulation session identifier owned by lotus-core.",
        examples=["sess_1"],
    )
    session_version: int = Field(
        description="Current simulation session version after the latest mutation.",
        examples=[2],
    )
    projected_positions: list[WorkbenchProjectedPositionView] = Field(
        default_factory=list,
        description="Projected positions published for the sandbox session.",
    )
    projected_summary: WorkbenchProjectedSummary = Field(
        description="Projected holdings summary for the sandbox session."
    )
    policy_feedback: WorkbenchPolicyFeedback | None = Field(
        default=None,
        description="Optional policy evaluation result returned after sandbox mutation.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Machine-readable sandbox warnings preserved by gateway.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description="Upstream partial failures preserved for sandbox diagnostics.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-workbench-sandbox-1",
                "contract_version": "v1",
                "portfolio_id": "PF_1001",
                "session_id": "sess_1",
                "session_version": 2,
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
                "policy_feedback": {
                    "status": "PASS",
                    "detail": "Simulation passed portfolio policy checks.",
                    "raw": {
                        "status": "COMPLETED",
                        "gate_decision": {
                            "status": "PASS",
                            "reason_code": "ALL_CHECKS_PASSED",
                        },
                    },
                },
                "warnings": [],
                "partial_failures": [],
            }
        }
    }
