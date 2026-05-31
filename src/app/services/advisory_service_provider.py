from app.services.advisor_cockpit_service import AdvisorCockpitService
from app.services.advisory_policy_service import AdvisoryPolicyService
from app.services.advisory_service_factory import (
    advisory_service_signature,
    build_advisor_cockpit_service,
    build_advisory_policy_service,
    build_advisory_workspace_service,
    build_bank_demo_proof_service,
    build_proposal_service,
)
from app.services.advisory_workspace_service import AdvisoryWorkspaceService
from app.services.bank_demo_proof_service import BankDemoProofService
from app.services.proposal_service import ProposalService

_ADVISORY_POLICY_SERVICE: AdvisoryPolicyService | None = None
_ADVISORY_POLICY_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_ADVISORY_WORKSPACE_SERVICE: AdvisoryWorkspaceService | None = None
_ADVISORY_WORKSPACE_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_ADVISOR_COCKPIT_SERVICE: AdvisorCockpitService | None = None
_ADVISOR_COCKPIT_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_BANK_DEMO_PROOF_SERVICE: BankDemoProofService | None = None
_BANK_DEMO_PROOF_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_PROPOSAL_SERVICE: ProposalService | None = None
_PROPOSAL_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def advisory_policy_service() -> AdvisoryPolicyService:
    global _ADVISORY_POLICY_SERVICE, _ADVISORY_POLICY_SERVICE_SIGNATURE
    signature = advisory_service_signature()
    if _ADVISORY_POLICY_SERVICE is None or _ADVISORY_POLICY_SERVICE_SIGNATURE != signature:
        _ADVISORY_POLICY_SERVICE = build_advisory_policy_service()
        _ADVISORY_POLICY_SERVICE_SIGNATURE = signature
    return _ADVISORY_POLICY_SERVICE


def advisory_workspace_service() -> AdvisoryWorkspaceService:
    global _ADVISORY_WORKSPACE_SERVICE, _ADVISORY_WORKSPACE_SERVICE_SIGNATURE
    signature = advisory_service_signature()
    if _ADVISORY_WORKSPACE_SERVICE is None or _ADVISORY_WORKSPACE_SERVICE_SIGNATURE != signature:
        _ADVISORY_WORKSPACE_SERVICE = build_advisory_workspace_service()
        _ADVISORY_WORKSPACE_SERVICE_SIGNATURE = signature
    return _ADVISORY_WORKSPACE_SERVICE


def advisor_cockpit_service() -> AdvisorCockpitService:
    global _ADVISOR_COCKPIT_SERVICE, _ADVISOR_COCKPIT_SERVICE_SIGNATURE
    signature = advisory_service_signature()
    if _ADVISOR_COCKPIT_SERVICE is None or _ADVISOR_COCKPIT_SERVICE_SIGNATURE != signature:
        _ADVISOR_COCKPIT_SERVICE = build_advisor_cockpit_service()
        _ADVISOR_COCKPIT_SERVICE_SIGNATURE = signature
    return _ADVISOR_COCKPIT_SERVICE


def bank_demo_proof_service() -> BankDemoProofService:
    global _BANK_DEMO_PROOF_SERVICE, _BANK_DEMO_PROOF_SERVICE_SIGNATURE
    signature = advisory_service_signature()
    if _BANK_DEMO_PROOF_SERVICE is None or _BANK_DEMO_PROOF_SERVICE_SIGNATURE != signature:
        _BANK_DEMO_PROOF_SERVICE = build_bank_demo_proof_service()
        _BANK_DEMO_PROOF_SERVICE_SIGNATURE = signature
    return _BANK_DEMO_PROOF_SERVICE


def proposal_service() -> ProposalService:
    global _PROPOSAL_SERVICE, _PROPOSAL_SERVICE_SIGNATURE
    signature = advisory_service_signature()
    if _PROPOSAL_SERVICE is None or _PROPOSAL_SERVICE_SIGNATURE != signature:
        _PROPOSAL_SERVICE = build_proposal_service()
        _PROPOSAL_SERVICE_SIGNATURE = signature
    return _PROPOSAL_SERVICE
