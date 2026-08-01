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

    normalized_role = required["X-Role"].upper()
    normalized_status = required["X-Principal-Status"].upper()
    capability_set = frozenset(
        part.strip() for part in required["X-Caller-Capabilities"].split(",") if part.strip()
    )
    normalized_legal_entity_code = required["X-Legal-Entity-Code"].upper()
    cleaned_authorized_proposal_id = _clean(authorized_proposal_id)
    cleaned_authorized_portfolio_id = _clean(authorized_portfolio_id)

    if normalized_status != "ACTIVE":
        _raise_access_error(
            status.HTTP_401_UNAUTHORIZED,
            "advisory_copilot_review_principal_invalid",
            "Advisory Copilot review requires an active trusted principal.",
        )
    if normalized_role not in ADVISORY_COPILOT_REVIEW_AUTHORIZED_ROLES:
        _raise_access_error(
            status.HTTP_403_FORBIDDEN,
            "advisory_copilot_review_access_denied",
            "Advisory Copilot review is not available for this role.",
        )
    if ADVISORY_COPILOT_REVIEW_CAPABILITY not in capability_set:
        _raise_access_error(
            status.HTTP_403_FORBIDDEN,
            "advisory_copilot_review_capability_required",
            "Advisory Copilot review requires advisory.copilot.review capability.",
        )
    identifiers = (
        required["X-Actor-Id"],
        required["X-Tenant-Id"],
        normalized_legal_entity_code,
        normalized_role,
        normalized_status,
        *capability_set,
    )
    optional_identifiers = (
        value
        for value in (cleaned_authorized_proposal_id, cleaned_authorized_portfolio_id)
        if value is not None
    )
    if any(
        not _IDENTIFIER_PATTERN.fullmatch(value) for value in (*identifiers, *optional_identifiers)
    ):
        _raise_access_error(
            status.HTTP_400_BAD_REQUEST,
            "advisory_copilot_review_caller_context_invalid",
            "Advisory Copilot review caller context is invalid.",
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
