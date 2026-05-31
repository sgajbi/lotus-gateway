from app.services.advisor_brief_service import AdvisorBriefService
from app.services.performance_workspace_service import PerformanceWorkspaceService
from app.services.risk_workspace_service import RiskWorkspaceService
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
    signature = workbench_service_signature()
    if _WORKBENCH_SERVICE is None or _WORKBENCH_SERVICE_SIGNATURE != signature:
        _WORKBENCH_SERVICE = build_workbench_service()
        _WORKBENCH_SERVICE_SIGNATURE = signature
    return _WORKBENCH_SERVICE


def performance_workspace_service() -> PerformanceWorkspaceService:
    global _PERFORMANCE_WORKSPACE_SERVICE, _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE
    signature = workbench_service_signature()
    if (
        _PERFORMANCE_WORKSPACE_SERVICE is None
        or _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE != signature
    ):
        _PERFORMANCE_WORKSPACE_SERVICE = build_performance_workspace_service(workbench_service())
        _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE = signature
    return _PERFORMANCE_WORKSPACE_SERVICE


def advisor_brief_service() -> AdvisorBriefService:
    global _ADVISOR_BRIEF_SERVICE, _ADVISOR_BRIEF_SERVICE_SIGNATURE
    signature = workbench_service_signature()
    if _ADVISOR_BRIEF_SERVICE is None or _ADVISOR_BRIEF_SERVICE_SIGNATURE != signature:
        _ADVISOR_BRIEF_SERVICE = build_advisor_brief_service(performance_workspace_service())
        _ADVISOR_BRIEF_SERVICE_SIGNATURE = signature
    return _ADVISOR_BRIEF_SERVICE


def risk_workspace_service() -> RiskWorkspaceService:
    global _RISK_WORKSPACE_SERVICE, _RISK_WORKSPACE_SERVICE_SIGNATURE
    signature = workbench_service_signature()
    if _RISK_WORKSPACE_SERVICE is None or _RISK_WORKSPACE_SERVICE_SIGNATURE != signature:
        _RISK_WORKSPACE_SERVICE = build_risk_workspace_service()
        _RISK_WORKSPACE_SERVICE_SIGNATURE = signature
    return _RISK_WORKSPACE_SERVICE
