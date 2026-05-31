from app.services.advise_client_factory import build_advise_client
from app.services.advisor_cockpit_service import AdvisorCockpitService
from app.services.advisory_policy_service import AdvisoryPolicyService
from app.services.advisory_workspace_service import AdvisoryWorkspaceService
from app.services.bank_demo_proof_service import BankDemoProofService
from app.services.proposal_service import ProposalService


def build_advisory_policy_service() -> AdvisoryPolicyService:
    return AdvisoryPolicyService(advise_client=build_advise_client())


def build_advisory_workspace_service() -> AdvisoryWorkspaceService:
    return AdvisoryWorkspaceService(advise_client=build_advise_client())


def build_advisor_cockpit_service() -> AdvisorCockpitService:
    return AdvisorCockpitService(advise_client=build_advise_client())


def build_bank_demo_proof_service() -> BankDemoProofService:
    return BankDemoProofService(advise_client=build_advise_client())


def build_proposal_service() -> ProposalService:
    return ProposalService(advise_client=build_advise_client())
