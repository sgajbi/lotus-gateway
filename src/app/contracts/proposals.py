from typing import Any, Literal

from pydantic import BaseModel, Field


class ProposalSimulateRequest(BaseModel):
    body: dict[str, Any] = Field(
        description="Opaque simulation request payload forwarded unchanged to lotus-manage.",
        examples=[
            {
                "portfolio_id": "PF_1001",
                "objective": "income",
                "constraints": {"max_cash_weight_pct": 5.0},
            }
        ],
    )


class ProposalSimulateResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-proposals-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the proposal simulation response.",
        examples=["v1"],
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Opaque lotus-manage simulation payload returned unchanged by gateway.",
        examples=[{"status": "READY", "proposal_run_id": "pr_1"}],
    )


class ProposalCreateRequest(BaseModel):
    body: dict[str, Any] = Field(
        description="Opaque proposal-create request payload forwarded unchanged to lotus-manage.",
        examples=[
            {
                "portfolio_id": "PF_1001",
                "proposal_name": "Income tilt rebalance",
                "created_by": "advisor_1",
            }
        ],
    )


class ProposalVersionCreateRequest(BaseModel):
    body: dict[str, Any] = Field(
        description=(
            "Opaque proposal-version request payload forwarded unchanged to lotus-manage."
        ),
        examples=[
            {
                "change_summary": "Reduce concentrated equity exposure.",
                "proposed_trades": [{"instrument_id": "EQ_1", "action": "SELL"}],
            }
        ],
    )


class ProposalSubmitRequest(BaseModel):
    actor_id: str = Field(
        description="Actor identifier requesting the submit transition.",
        examples=["advisor_1"],
    )
    expected_state: str = Field(
        default="DRAFT",
        description="Expected current state for optimistic concurrency check.",
        examples=["DRAFT"],
    )
    review_type: Literal["RISK", "COMPLIANCE"] = Field(
        default="RISK",
        description="First review stage that should receive the submitted proposal.",
        examples=["RISK"],
    )
    related_version_no: int | None = Field(
        default=None,
        description="Optional related version number for audit linkage.",
        examples=[2],
    )
    reason: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured reason payload captured in workflow event.",
        examples=[{"summary": "Client requested income tilt", "ticket_id": "REQ-102"}],
    )


class ProposalApprovalActionRequest(BaseModel):
    actor_id: str = Field(
        description="Actor identifier recording the approval or consent action.",
        examples=["risk_1"],
    )
    expected_state: str = Field(
        description="Expected current workflow state before the action is applied.",
        examples=["RISK_REVIEW"],
    )
    related_version_no: int | None = Field(
        default=None,
        description="Optional related version number for audit linkage.",
        examples=[2],
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured approval metadata/details.",
        examples=[{"decision": "APPROVED", "comment": "Within mandate"}],
    )


class ProposalEnvelopeResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-proposals-2"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the proposal envelope response.",
        examples=["v1"],
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Opaque lotus-manage proposal payload returned unchanged by gateway.",
        examples=[{"items": [{"proposal_id": "pp_1", "current_state": "DRAFT"}]}],
    )
