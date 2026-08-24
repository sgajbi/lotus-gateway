from typing import get_args

from app.contracts.proposal_decision_vocabulary import (
    CONTRACT_VERSION,
    SCHEMA_VERSION,
    SOURCE_SERVICE,
    load_proposal_decision_vocabulary,
)
from app.contracts.proposal_risk_impact_allocation import (
    ProposalRiskImpactDecisionStatus,
    ProposalRiskImpactGate,
)
from app.contracts.proposal_risk_impact_coherence import proposal_decision_vocabulary


def test_packaged_advise_vocabulary_is_the_runtime_coherence_policy() -> None:
    packaged = load_proposal_decision_vocabulary()

    assert proposal_decision_vocabulary() == packaged
    assert packaged.schema_version == SCHEMA_VERSION
    assert packaged.contract_version == CONTRACT_VERSION
    assert packaged.source_service == SOURCE_SERVICE
    assert set(packaged.decision_status_top_levels) == set(
        get_args(ProposalRiskImpactDecisionStatus)
    )
    assert set(packaged.workflow_gate_next_steps) == set(get_args(ProposalRiskImpactGate))


def test_client_consent_pairing_matches_the_source_owned_advise_contract() -> None:
    vocabulary = proposal_decision_vocabulary()

    assert vocabulary.decision_status_next_actions["REQUIRES_CLIENT_CONSENT"] == frozenset(
        {"DISCUSS_WITH_CLIENT"}
    )
    assert vocabulary.decision_status_workflow_gates["REQUIRES_CLIENT_CONSENT"] == frozenset(
        {"CLIENT_CONSENT_REQUIRED"}
    )
    assert (
        vocabulary.workflow_gate_next_steps["CLIENT_CONSENT_REQUIRED"] == "REQUEST_CLIENT_CONSENT"
    )
