from app.services.advisor_brief_service import AdvisorBriefService
from app.services.performance_workspace_service import PerformanceWorkspaceService
from app.services.risk_workspace_service import RiskWorkspaceService
from app.services.service_provider_cache import resolve_cached_service
from app.services.workbench_service import WorkbenchService
from app.services.workbench_service_factory import (
    build_advisor_brief_service,
    build_performance_workspace_service,
    build_risk_workspace_service,
    build_workbench_service,
    workbench_service_signature,
)

_WORKBENCH_SERVICE: WorkbenchService | None = None
_WORKBENCH_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_PERFORMANCE_WORKSPACE_SERVICE: PerformanceWorkspaceService | None = None
_PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_ADVISOR_BRIEF_SERVICE: AdvisorBriefService | None = None
_ADVISOR_BRIEF_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_RISK_WORKSPACE_SERVICE: RiskWorkspaceService | None = None
_RISK_WORKSPACE_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def workbench_service() -> WorkbenchService:
    global _WORKBENCH_SERVICE, _WORKBENCH_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _WORKBENCH_SERVICE,
        _WORKBENCH_SERVICE_SIGNATURE,
        workbench_service_signature(),
        build_workbench_service,
    )
    _WORKBENCH_SERVICE = service
    _WORKBENCH_SERVICE_SIGNATURE = signature
    return service


def performance_workspace_service() -> PerformanceWorkspaceService:
    global _PERFORMANCE_WORKSPACE_SERVICE, _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _PERFORMANCE_WORKSPACE_SERVICE,
        _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE,
        workbench_service_signature(),
        lambda: build_performance_workspace_service(workbench_service()),
    )
    _PERFORMANCE_WORKSPACE_SERVICE = service
    _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE = signature
    return service


def advisor_brief_service() -> AdvisorBriefService:
    global _ADVISOR_BRIEF_SERVICE, _ADVISOR_BRIEF_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _ADVISOR_BRIEF_SERVICE,
        _ADVISOR_BRIEF_SERVICE_SIGNATURE,
        workbench_service_signature(),
        lambda: build_advisor_brief_service(performance_workspace_service()),
    )
    _ADVISOR_BRIEF_SERVICE = service
    _ADVISOR_BRIEF_SERVICE_SIGNATURE = signature
    return service


def risk_workspace_service() -> RiskWorkspaceService:
    global _RISK_WORKSPACE_SERVICE, _RISK_WORKSPACE_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _RISK_WORKSPACE_SERVICE,
        _RISK_WORKSPACE_SERVICE_SIGNATURE,
        workbench_service_signature(),
        build_risk_workspace_service,
    )
    _RISK_WORKSPACE_SERVICE = service
    _RISK_WORKSPACE_SERVICE_SIGNATURE = signature
    return service
