from app.services.advisor_cockpit_service import AdvisorCockpitService
from app.services.advisory_policy_service import AdvisoryPolicyService
from app.services.advisory_service_factory import (
    build_advisor_cockpit_service,
    build_advisory_policy_service,
    build_advisory_workspace_service,
    build_bank_demo_proof_service,
    build_proposal_service,
)
from app.services.advisory_workspace_service import AdvisoryWorkspaceService
from app.services.bank_demo_proof_service import BankDemoProofService
from app.services.proposal_service import ProposalService


def advisory_policy_service() -> AdvisoryPolicyService:
    return build_advisory_policy_service()


def advisory_workspace_service() -> AdvisoryWorkspaceService:
    return build_advisory_workspace_service()


def advisor_cockpit_service() -> AdvisorCockpitService:
    return build_advisor_cockpit_service()


def bank_demo_proof_service() -> BankDemoProofService:
    return build_bank_demo_proof_service()


def proposal_service() -> ProposalService:
    return build_proposal_service()
