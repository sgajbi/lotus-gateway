from typing import Any

from pydantic import BaseModel, Field


class ProposalSimulateRequest(BaseModel):
    body: dict[str, Any] = Field(
        description="Opaque simulation request payload forwarded unchanged to lotus-advise.",
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
    data: "ProposalSimulationData" = Field(
        description="Proposal simulation payload returned by lotus-advise.",
    )


class ProposalSimulationData(BaseModel):
    proposal_run_id: str = Field(
        description="Proposal simulation run identifier.",
        examples=["pr_1"],
    )
    correlation_id: str = Field(
        description="Correlation identifier emitted by the simulation engine.",
        examples=["corr_engine_1"],
    )
    status: str = Field(
        description="Top-level domain outcome for the simulated proposal.",
        examples=["READY"],
    )
    before: dict[str, Any] = Field(
        default_factory=dict,
        description="Before-state valuation snapshot used as the simulation baseline.",
        examples=[{"portfolio_value": {"amount": "100000.00", "currency": "USD"}}],
    )
    intents: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Deterministically ordered proposal intents applied during simulation.",
        examples=[
            [
                {
                    "intent_type": "CASH_FLOW",
                    "intent_id": "oi_cf_1",
                    "currency": "USD",
                    "amount": "2000.00",
                },
                {
                    "intent_type": "SECURITY_TRADE",
                    "intent_id": "oi_1",
                    "side": "BUY",
                    "instrument_id": "EQ_GROWTH",
                    "quantity": "40",
                },
            ]
        ],
    )
    after_simulated: dict[str, Any] = Field(
        default_factory=dict,
        description="After-state valuation snapshot after all proposal intents are applied.",
        examples=[{"portfolio_value": {"amount": "102000.00", "currency": "USD"}}],
    )
    reconciliation: dict[str, Any] | None = Field(
        default=None,
        description="Optional reconciliation output comparing before and after states.",
        examples=[{"cash_balance_delta": {"amount": "2000.00", "currency": "USD"}}],
    )
    rule_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Rule-engine evaluations produced during simulation.",
        examples=[[{"rule_id": "CASH_BAND", "severity": "SOFT", "status": "PASS"}]],
    )
    explanation: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional explanatory payload emitted by the simulation engine.",
        examples=[{"summary": "Proposal remains within mandate concentration limits."}],
    )
    diagnostics: dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnostics and warning payload for the simulation run.",
        examples=[
            {
                "warnings": [],
                "data_quality": {"price_missing": [], "fx_missing": []},
            }
        ],
    )
    drift_analysis: dict[str, Any] | None = Field(
        default=None,
        description="Optional reference-model drift analytics when supplied upstream.",
        examples=[{"tracking_error_pct": 1.2}],
    )
    suitability: dict[str, Any] | None = Field(
        default=None,
        description="Optional advisory suitability scanner output.",
        examples=[{"status": "PASS", "issues": []}],
    )
    gate_decision: dict[str, Any] | None = Field(
        default=None,
        description="Deterministic workflow gate decision for advisory routing.",
        examples=[
            {"gate": "CLIENT_CONSENT_REQUIRED", "recommended_next_step": "REQUEST_CLIENT_CONSENT"}
        ],
    )
    lineage: dict[str, Any] = Field(
        default_factory=dict,
        description="Lineage identifiers and request hash for the simulation run.",
        examples=[{"request_hash": "sha256:req-1", "idempotency_key": "idem-simulate-1"}],
    )
