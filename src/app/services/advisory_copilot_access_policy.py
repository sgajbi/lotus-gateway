"""Admit Advisory Copilot authority before forwarding a tenant-owned request.

Gateway validates the operation-specific role, capability, active-principal posture,
and resource scope supplied by its caller. It forwards only the capability exercised
by the operation and its own true service identity; it never invents a user, tenant,
legal entity, role, or resource grant.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from fastapi import HTTPException, status

_CALLER_ROLES = frozenset({"ADVISOR", "COMPLIANCE_REVIEWER", "POLICY_CHECKER"})
_READ_ROLES = _CALLER_ROLES | frozenset({"ADVISORY_SUPERVISOR"})
_REVIEW_ROLES = frozenset({"ADVISORY_SUPERVISOR", "COMPLIANCE_REVIEWER", "POLICY_CHECKER"})
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


@dataclass(frozen=True)
class AdvisoryCopilotOperation:
    name: str
    capability: str
    permitted_roles: frozenset[str]
    requires_proposal_scope: bool = False
    requires_portfolio_scope: bool = True


COPILOT_PACKET_CREATE = AdvisoryCopilotOperation(
    name="packet.create",
    capability="advisory.copilot.packet",
    permitted_roles=_CALLER_ROLES,
)
COPILOT_PROPOSAL_PACKET_CREATE = AdvisoryCopilotOperation(
    name="proposal_packet.create",
    capability="advisory.policy_evaluation.read",
    permitted_roles=_CALLER_ROLES,
    requires_proposal_scope=True,
)
COPILOT_ACTION_RUN = AdvisoryCopilotOperation(
    name="action.run",
    capability="advisory.copilot.action",
    permitted_roles=_CALLER_ROLES,
)
COPILOT_RESOURCE_READ = AdvisoryCopilotOperation(
    name="resource.read",
    capability="advisory.copilot.read",
    permitted_roles=_READ_ROLES,
    # A trusted BFF uses the tenant-scoped read to resolve a packet/run's stored
    # portfolio before it admits a later scoped mutation. Advise still fences
    # the lookup by the admitted tenant; an optional portfolio selector is
    # forwarded when the caller already knows it.
    requires_portfolio_scope=False,
)
COPILOT_PROPOSAL_RUNS_READ = AdvisoryCopilotOperation(
    name="proposal_runs.read",
    capability="advisory.copilot.read",
    permitted_roles=_READ_ROLES,
    requires_proposal_scope=True,
    requires_portfolio_scope=False,
)
COPILOT_REVIEW = AdvisoryCopilotOperation(
    name="review",
    capability="advisory.copilot.review",
    permitted_roles=_REVIEW_ROLES,
    requires_proposal_scope=True,
)


@dataclass(frozen=True)
class AdvisoryCopilotCallerContext:
    actor_id: str
    tenant_id: str
    legal_entity_code: str
    role: str
    capability: str
    principal_status: str
    authorized_proposal_id: str | None
    authorized_portfolio_id: str | None

    def upstream_headers(self) -> dict[str, str]:
        headers = {
            "X-Actor-Id": self.actor_id,
            "X-Role": self.role,
            "X-Tenant-Id": self.tenant_id,
            "X-Legal-Entity-Code": self.legal_entity_code,
            "X-Service-Identity": "lotus-gateway",
            "X-Capabilities": self.capability,
            "X-Principal-Status": self.principal_status,
        }
        if self.authorized_portfolio_id is not None:
            headers["X-Authorized-Portfolio-Id"] = self.authorized_portfolio_id
        if self.authorized_proposal_id is not None:
            headers["X-Authorized-Proposal-Id"] = self.authorized_proposal_id
        return headers


def require_advisory_copilot_caller_context(
    *,
    operation: AdvisoryCopilotOperation,
    actor_id: str | None,
    tenant_id: str | None,
    legal_entity_code: str | None,
    role: str | None,
    capabilities: str | None,
    principal_status: str | None,
    authorized_proposal_id: str | None,
    authorized_portfolio_id: str | None,
) -> AdvisoryCopilotCallerContext:
    required = _required_context_values(
        operation=operation,
        actor_id=actor_id,
        tenant_id=tenant_id,
        legal_entity_code=legal_entity_code,
        role=role,
        capabilities=capabilities,
        principal_status=principal_status,
    )
    normalized_role, normalized_status = _require_operation_access(
        operation=operation,
        required=required,
    )
    proposal_id, portfolio_id = _require_operation_scope(
        operation=operation,
        authorized_proposal_id=authorized_proposal_id,
        authorized_portfolio_id=authorized_portfolio_id,
    )
    normalized_legal_entity = required["X-Legal-Entity-Code"].upper()
    _require_valid_identifiers(
        operation=operation,
        required=required,
        normalized_values=(normalized_legal_entity, normalized_role, normalized_status),
        resource_scope=(proposal_id, portfolio_id),
    )

    return AdvisoryCopilotCallerContext(
        actor_id=required["X-Actor-Id"],
        tenant_id=required["X-Tenant-Id"],
        legal_entity_code=normalized_legal_entity,
        role=normalized_role,
        capability=operation.capability,
        principal_status=normalized_status,
        authorized_proposal_id=proposal_id,
        authorized_portfolio_id=portfolio_id,
    )


def _require_operation_access(
    *,
    operation: AdvisoryCopilotOperation,
    required: dict[str, str],
) -> tuple[str, str]:
    normalized_role = required["X-Role"].upper()
    normalized_status = required["X-Principal-Status"].upper()
    capabilities = frozenset(
        part.strip() for part in required["X-Caller-Capabilities"].split(",") if part.strip()
    )
    if normalized_status != "ACTIVE":
        _raise_access_error(
            status.HTTP_401_UNAUTHORIZED,
            _error_code(operation, "principal_invalid"),
            "Advisory Copilot requires an active trusted principal.",
        )
    if normalized_role not in operation.permitted_roles:
        _raise_access_error(
            status.HTTP_403_FORBIDDEN,
            _error_code(operation, "access_denied"),
            "Advisory Copilot access is not available for this caller.",
        )
    if operation.capability not in capabilities:
        code = (
            "advisory_copilot_review_capability_required"
            if operation is COPILOT_REVIEW
            else "advisory_copilot_access_denied"
        )
        _raise_access_error(
            status.HTTP_403_FORBIDDEN,
            code,
            "Advisory Copilot access is not available for this caller.",
        )
    return normalized_role, normalized_status


def _require_operation_scope(
    *,
    operation: AdvisoryCopilotOperation,
    authorized_proposal_id: str | None,
    authorized_portfolio_id: str | None,
) -> tuple[str | None, str | None]:
    proposal_id = _clean(authorized_proposal_id)
    portfolio_id = _clean(authorized_portfolio_id)
    missing_scope = []
    if operation.requires_proposal_scope and proposal_id is None:
        missing_scope.append("X-Authorized-Proposal-Id")
    if operation.requires_portfolio_scope and portfolio_id is None:
        missing_scope.append("X-Authorized-Portfolio-Id")
    if missing_scope:
        _raise_access_error(
            status.HTTP_403_FORBIDDEN,
            _error_code(operation, "scope_required"),
            "Advisory Copilot requires trusted resource scope.",
            missing_headers=missing_scope,
        )
    return proposal_id, portfolio_id


def _require_valid_identifiers(
    *,
    operation: AdvisoryCopilotOperation,
    required: dict[str, str],
    normalized_values: tuple[str, str, str],
    resource_scope: tuple[str | None, str | None],
) -> None:
    identifier_values = (
        required["X-Actor-Id"],
        required["X-Tenant-Id"],
        *normalized_values,
        operation.capability,
        *(value for value in resource_scope if value is not None),
    )
    if any(not _IDENTIFIER_PATTERN.fullmatch(value) for value in identifier_values):
        _raise_access_error(
            status.HTTP_400_BAD_REQUEST,
            _error_code(operation, "caller_context_invalid"),
            "Advisory Copilot caller context is invalid.",
        )


def _required_context_values(
    *,
    operation: AdvisoryCopilotOperation,
    actor_id: str | None,
    tenant_id: str | None,
    legal_entity_code: str | None,
    role: str | None,
    capabilities: str | None,
    principal_status: str | None,
) -> dict[str, str]:
    required = {
        "X-Actor-Id": _clean(actor_id),
        "X-Tenant-Id": _clean(tenant_id),
        "X-Legal-Entity-Code": _clean(legal_entity_code),
        "X-Role": _clean(role),
        "X-Caller-Capabilities": _clean(capabilities),
        "X-Principal-Status": _clean(principal_status),
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        _raise_access_error(
            status.HTTP_400_BAD_REQUEST,
            _error_code(operation, "caller_context_missing"),
            "Required Advisory Copilot caller context is missing.",
            missing_headers=missing,
        )
    return {name: value for name, value in required.items() if value is not None}


def _error_code(operation: AdvisoryCopilotOperation, suffix: str) -> str:
    prefix = "advisory_copilot_review" if operation is COPILOT_REVIEW else "advisory_copilot"
    return f"{prefix}_{suffix}"


def _raise_access_error(
    status_code: int,
    code: str,
    message: str,
    *,
    missing_headers: list[str] | None = None,
) -> None:
    detail: dict[str, object] = {"code": code, "message": message}
    if missing_headers is not None:
        detail["missing_headers"] = missing_headers
    raise HTTPException(status_code=status_code, detail=detail)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
