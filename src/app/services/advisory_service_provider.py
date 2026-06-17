from app.services.advisor_cockpit_service import AdvisorCockpitService
from app.services.advisory_copilot_service import AdvisoryCopilotService
from app.services.advisory_policy_service import AdvisoryPolicyService
from app.services.advisory_service_factory import (
    advisory_service_signature,
    build_advisor_cockpit_service,
    build_advisory_copilot_service,
    build_advisory_policy_service,
    build_advisory_workspace_service,
    build_bank_demo_proof_service,
    build_proposal_service,
)
from app.services.advisory_workspace_service import AdvisoryWorkspaceService
from app.services.bank_demo_proof_service import BankDemoProofService
from app.services.proposal_service import ProposalService
from app.services.service_provider_cache import resolve_cached_service

_ADVISORY_POLICY_SERVICE: AdvisoryPolicyService | None = None
_ADVISORY_POLICY_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_ADVISORY_COPILOT_SERVICE: AdvisoryCopilotService | None = None
_ADVISORY_COPILOT_SERVICE_SIGNATURE: tuple[object, ...] | None = None
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
    service, signature = resolve_cached_service(
        _ADVISORY_POLICY_SERVICE,
        _ADVISORY_POLICY_SERVICE_SIGNATURE,
        advisory_service_signature(),
        build_advisory_policy_service,
    )
    _ADVISORY_POLICY_SERVICE = service
    _ADVISORY_POLICY_SERVICE_SIGNATURE = signature
    return service


def advisory_copilot_service() -> AdvisoryCopilotService:
    global _ADVISORY_COPILOT_SERVICE, _ADVISORY_COPILOT_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _ADVISORY_COPILOT_SERVICE,
        _ADVISORY_COPILOT_SERVICE_SIGNATURE,
        advisory_service_signature(),
        build_advisory_copilot_service,
    )
    _ADVISORY_COPILOT_SERVICE = service
    _ADVISORY_COPILOT_SERVICE_SIGNATURE = signature
    return service


def advisory_workspace_service() -> AdvisoryWorkspaceService:
    global _ADVISORY_WORKSPACE_SERVICE, _ADVISORY_WORKSPACE_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _ADVISORY_WORKSPACE_SERVICE,
        _ADVISORY_WORKSPACE_SERVICE_SIGNATURE,
        advisory_service_signature(),
        build_advisory_workspace_service,
    )
    _ADVISORY_WORKSPACE_SERVICE = service
    _ADVISORY_WORKSPACE_SERVICE_SIGNATURE = signature
    return service


def advisor_cockpit_service() -> AdvisorCockpitService:
    global _ADVISOR_COCKPIT_SERVICE, _ADVISOR_COCKPIT_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _ADVISOR_COCKPIT_SERVICE,
        _ADVISOR_COCKPIT_SERVICE_SIGNATURE,
        advisory_service_signature(),
        build_advisor_cockpit_service,
    )
    _ADVISOR_COCKPIT_SERVICE = service
    _ADVISOR_COCKPIT_SERVICE_SIGNATURE = signature
    return service


def bank_demo_proof_service() -> BankDemoProofService:
    global _BANK_DEMO_PROOF_SERVICE, _BANK_DEMO_PROOF_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _BANK_DEMO_PROOF_SERVICE,
        _BANK_DEMO_PROOF_SERVICE_SIGNATURE,
        advisory_service_signature(),
        build_bank_demo_proof_service,
    )
    _BANK_DEMO_PROOF_SERVICE = service
    _BANK_DEMO_PROOF_SERVICE_SIGNATURE = signature
    return service


def proposal_service() -> ProposalService:
    global _PROPOSAL_SERVICE, _PROPOSAL_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _PROPOSAL_SERVICE,
        _PROPOSAL_SERVICE_SIGNATURE,
        advisory_service_signature(),
        build_proposal_service,
    )
    _PROPOSAL_SERVICE = service
    _PROPOSAL_SERVICE_SIGNATURE = signature
    return service
