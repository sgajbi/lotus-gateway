from typing import Any

from app.contracts.workbench import WorkbenchPolicyFeedback, WorkbenchProjectedPositionView


def build_policy_simulation_payload(
    *,
    portfolio_id: str,
    base_currency: str,
    projected_positions: list[WorkbenchProjectedPositionView],
) -> dict[str, Any]:
    return {
        "portfolio_snapshot": {
            "portfolio_id": portfolio_id,
            "base_currency": base_currency,
            "positions": [
                {
                    "instrument_id": row.security_id,
                    "quantity": f"{row.proposed_quantity:.4f}",
                }
                for row in projected_positions
                if row.proposed_quantity > 0
            ],
            "cash_balances": [],
        },
        "market_data_snapshot": {"prices": [], "fx_rates": []},
        "shelf_entries": [],
        "options": {
            "enable_proposal_simulation": True,
            "proposal_apply_cash_flows_first": True,
            "proposal_block_negative_cash": True,
        },
        "proposed_cash_flows": [],
        "proposed_trades": [],
    }


def build_policy_idempotency_key(*, session_id: str, session_version: int) -> str:
    return f"sandbox-{session_id}-{session_version}"


def parse_policy_feedback_success(payload: dict[str, Any]) -> WorkbenchPolicyFeedback:
    gate_decision = payload.get("gate_decision")
    if isinstance(gate_decision, dict):
        gate_status = str(gate_decision.get("status", "UNKNOWN"))
        return WorkbenchPolicyFeedback(
            status=gate_status,
            detail=str(gate_decision.get("reason_code", "")) or None,
            raw=payload,
        )
    return WorkbenchPolicyFeedback(
        status=str(payload.get("status", "AVAILABLE")),
        detail=None,
        raw=payload,
    )


def parse_policy_feedback_unavailable(payload: Any) -> WorkbenchPolicyFeedback:
    return WorkbenchPolicyFeedback(
        status="UNAVAILABLE",
        detail="Proposal simulation unavailable",
        raw=payload if isinstance(payload, dict) else None,
    )
