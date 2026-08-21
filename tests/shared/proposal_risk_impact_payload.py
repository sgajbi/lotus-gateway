from copy import deepcopy


def build_proposal_risk_impact_source_payload(
    *,
    proposal_id: str = "pp_risk_001",
    portfolio_id: str = "PB_SG_GLOBAL_BAL_001",
) -> dict[str, object]:
    allocation_lens = {
        "contract_version": "advisory-simulation.v1",
        "calculator_version": "lotus-core.allocation-calculator.v1",
        "source": "LOTUS_CORE",
        "dimensions": ["asset_class"],
    }
    current_view = {
        "dimension": "asset_class",
        "total_value": {"amount": "1250000.00", "currency": "USD"},
        "buckets": [
            {
                "key": "EQUITY",
                "weight": "0.6800",
                "value": {"amount": "850000.00", "currency": "USD"},
                "position_count": 12,
            },
            {
                "key": "CASH",
                "weight": "0.3200",
                "value": {"amount": "400000.00", "currency": "USD"},
                "position_count": 1,
            },
        ],
    }
    proposed_view = {
        "dimension": "asset_class",
        "total_value": {"amount": "1250000.00", "currency": "USD"},
        "buckets": [
            {
                "key": "EQUITY",
                "weight": "0.6200",
                "value": {"amount": "775000.00", "currency": "USD"},
                "position_count": 13,
            },
            {
                "key": "CASH",
                "weight": "0.3800",
                "value": {"amount": "475000.00", "currency": "USD"},
                "position_count": 1,
            },
        ],
    }
    decision = {
        "decision_status": "REQUIRES_RISK_REVIEW",
        "top_level_status": "PENDING_REVIEW",
        "primary_reason_code": "MATERIAL_CONCENTRATION_CHANGE",
        "primary_summary": "Review the proposed reduction in concentrated equity exposure.",
        "recommended_next_action": "REVIEW_RISK",
        "decision_policy_version": "proposal-decision.2026-04",
        "confidence": "HIGH",
        "approval_requirements": [
            {
                "approval_type": "RISK_REVIEW",
                "required": True,
                "severity": "HIGH",
                "reason_code": "MATERIAL_CONCENTRATION_CHANGE",
                "summary": "Risk review is required before client discussion.",
                "blocking_until_approved": True,
                "evidence_refs": ["artifact.risk_lens"],
                "policy_version": "proposal-decision.2026-04",
            }
        ],
        "material_changes": [
            {
                "change_id": "mc_concentration_001",
                "family": "CONCENTRATION_CHANGE",
                "severity": "HIGH",
                "before": {"weight": "0.6800"},
                "after": {"weight": "0.6200"},
                "delta": {"weight": "-0.0600"},
                "summary": "Equity concentration reduces by six percentage points.",
                "evidence_refs": ["proposal_result.before", "proposal_result.after_simulated"],
            }
        ],
        "missing_evidence": [],
        "risk_posture": {
            "status": "AVAILABLE",
            "source_service": "lotus-risk",
            "summary": "Concentration reduces, with residual issuer risk requiring review.",
        },
        "evidence_refs": ["artifact.risk_lens", "proposal_result.allocation_views"],
    }
    risk_lens = {
        "status": "AVAILABLE",
        "source_service": "lotus-risk",
        "summary": "Concentration reduces, with residual issuer risk requiring review.",
        "highlights": [
            "Equity weight reduces from 68% to 62%.",
            "Residual single-issuer concentration remains subject to risk review.",
        ],
    }
    gate = {
        "gate": "RISK_REVIEW_REQUIRED",
        "recommended_next_step": "RISK_REVIEW",
        "reasons": [
            {
                "reason_code": "MATERIAL_CONCENTRATION_CHANGE",
                "severity": "HIGH",
                "source": "RULE_ENGINE",
                "details": {},
            }
        ],
        "summary": {
            "hard_fail_count": 0,
            "soft_fail_count": 1,
            "new_high_suitability_count": 0,
            "new_medium_suitability_count": 0,
        },
    }
    return {
        "proposal": {
            "proposal_id": proposal_id,
            "portfolio_id": portfolio_id,
            "title": "Reduce concentrated equity exposure",
            "current_state": "RISK_REVIEW",
            "current_version_no": 2,
        },
        "current_version": {
            "proposal_version_id": "ppv_risk_002",
            "proposal_id": proposal_id,
            "version_no": 2,
            "created_at": "2026-08-21T08:30:00Z",
            "request_hash": "sha256:risk-request-002",
            "artifact_hash": "sha256:risk-artifact-002",
            "simulation_hash": "sha256:risk-simulation-002",
            "proposal_result": {
                "before": {"allocation_views": [current_view]},
                "after_simulated": {"allocation_views": [proposed_view]},
                "allocation_lens": allocation_lens,
                "proposal_decision_summary": decision,
                "gate_decision": gate,
            },
            "artifact": {
                "risk_lens": risk_lens,
                "proposal_decision_summary": deepcopy(decision),
                "gate_decision": deepcopy(gate),
            },
            "gate_decision": deepcopy(gate),
        },
        "last_gate_decision": deepcopy(gate),
    }


__all__ = ["build_proposal_risk_impact_source_payload"]
