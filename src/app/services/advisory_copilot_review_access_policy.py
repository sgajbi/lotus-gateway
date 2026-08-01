import re
from dataclasses import dataclass

from fastapi import HTTPException, status

ADVISORY_COPILOT_REVIEW_CAPABILITY = "advisory.copilot.review"
ADVISORY_COPILOT_REVIEW_AUTHORIZED_ROLES = frozenset(
    {"ADVISORY_SUPERVISOR", "COMPLIANCE_REVIEWER", "POLICY_CHECKER"}
)

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


@dataclass(frozen=True)
class AdvisoryCopilotReviewCallerContext:
    actor_id: str
    tenant_id: str
    legal_entity_code: str
    role: str
    capabilities: frozenset[str]
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
            "X-Capabilities": ",".join(sorted(self.capabilities)),
            "X-Principal-Status": self.principal_status,
        }
        if self.authorized_proposal_id is not None:
            headers["X-Authorized-Proposal-Id"] = self.authorized_proposal_id
        if self.authorized_portfolio_id is not None:
            headers["X-Authorized-Portfolio-Id"] = self.authorized_portfolio_id
        return headers


def require_advisory_copilot_review_caller_context(
    *,
    actor_id: str | None,
    tenant_id: str | None,
    legal_entity_code: str | None,
    role: str | None,
    capabilities: str | None,
    principal_status: str | None,
    authorized_proposal_id: str | None,
    authorized_portfolio_id: str | None,
) -> AdvisoryCopilotReviewCallerContext:
    required = _required_context_values(
        actor_id=actor_id,
        tenant_id=tenant_id,
        legal_entity_code=legal_entity_code,
        role=role,
        capabilities=capabilities,
        principal_status=principal_status,
    )
    normalized_role = _require_allowed_role(required["X-Role"])
    normalized_status = _require_active_principal(required["X-Principal-Status"])
    capability_set = _require_review_capability(required["X-Caller-Capabilities"])
    normalized_legal_entity_code = required["X-Legal-Entity-Code"].upper()
    cleaned_authorized_proposal_id = _clean(authorized_proposal_id)
    cleaned_authorized_portfolio_id = _clean(authorized_portfolio_id)
    _require_resource_scope(
        authorized_proposal_id=cleaned_authorized_proposal_id,
        authorized_portfolio_id=cleaned_authorized_portfolio_id,
    )
    _require_valid_identifiers(
        required=required,
        normalized_legal_entity_code=normalized_legal_entity_code,
        normalized_role=normalized_role,
        normalized_status=normalized_status,
        capability_set=capability_set,
        optional_values=(cleaned_authorized_proposal_id, cleaned_authorized_portfolio_id),
    )

    return AdvisoryCopilotReviewCallerContext(
        actor_id=required["X-Actor-Id"],
        tenant_id=required["X-Tenant-Id"],
        legal_entity_code=normalized_legal_entity_code,
        role=normalized_role,
        capabilities=capability_set,
        principal_status=normalized_status,
        authorized_proposal_id=cleaned_authorized_proposal_id,
        authorized_portfolio_id=cleaned_authorized_portfolio_id,
    )


def _require_resource_scope(
    *,
    authorized_proposal_id: str | None,
    authorized_portfolio_id: str | None,
) -> None:
    missing = [
        header_name
        for header_name, value in (
            ("X-Authorized-Proposal-Id", authorized_proposal_id),
            ("X-Authorized-Portfolio-Id", authorized_portfolio_id),
        )
        if value is None
    ]
    if missing:
        _raise_access_error(
            status.HTTP_403_FORBIDDEN,
            "advisory_copilot_review_scope_required",
            "Advisory Copilot review requires trusted proposal and portfolio scope.",
            missing_headers=missing,
        )


def _required_context_values(
    *,
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
            "advisory_copilot_review_caller_context_missing",
            "Required Advisory Copilot review caller context is missing.",
            missing_headers=missing,
        )
    return {name: value for name, value in required.items() if value is not None}


def _require_active_principal(principal_status: str) -> str:
    normalized_status = principal_status.upper()
    if normalized_status != "ACTIVE":
        _raise_access_error(
            status.HTTP_401_UNAUTHORIZED,
            "advisory_copilot_review_principal_invalid",
            "Advisory Copilot review requires an active trusted principal.",
        )
    return normalized_status


def _require_allowed_role(role: str) -> str:
    normalized_role = role.upper()
    if normalized_role not in ADVISORY_COPILOT_REVIEW_AUTHORIZED_ROLES:
        _raise_access_error(
            status.HTTP_403_FORBIDDEN,
            "advisory_copilot_review_access_denied",
            "Advisory Copilot review is not available for this role.",
        )
    return normalized_role


def _require_review_capability(capabilities: str) -> frozenset[str]:
    capability_set = frozenset(part.strip() for part in capabilities.split(",") if part.strip())
    if ADVISORY_COPILOT_REVIEW_CAPABILITY not in capability_set:
        _raise_access_error(
            status.HTTP_403_FORBIDDEN,
            "advisory_copilot_review_capability_required",
            "Advisory Copilot review requires advisory.copilot.review capability.",
        )
    return capability_set


def _require_valid_identifiers(
    *,
    required: dict[str, str],
    normalized_legal_entity_code: str,
    normalized_role: str,
    normalized_status: str,
    capability_set: frozenset[str],
    optional_values: tuple[str | None, str | None],
) -> None:
    identifiers = (
        required["X-Actor-Id"],
        required["X-Tenant-Id"],
        normalized_legal_entity_code,
        normalized_role,
        normalized_status,
        *capability_set,
        *(value for value in optional_values if value is not None),
    )
    if any(not _IDENTIFIER_PATTERN.fullmatch(value) for value in identifiers):
        _raise_access_error(
            status.HTTP_400_BAD_REQUEST,
            "advisory_copilot_review_caller_context_invalid",
            "Advisory Copilot review caller context is invalid.",
        )


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
