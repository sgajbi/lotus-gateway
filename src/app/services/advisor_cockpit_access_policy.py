import re
from dataclasses import dataclass
from typing import cast, get_args

from app.contracts.advisor_cockpit import AdvisorCockpitOwnerRole

ADVISOR_COCKPIT_READ_CAPABILITY = "advisory.advisor_cockpit.read"
ADVISOR_COCKPIT_ACKNOWLEDGE_CAPABILITY = "advisory.advisor_cockpit.acknowledge"

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SUPPORTED_ROLES = frozenset(get_args(AdvisorCockpitOwnerRole))


@dataclass(frozen=True)
class AdvisorCockpitCallerContext:
    actor_id: str
    caller_application: str
    tenant_id: str
    region: str
    booking_center_code: str
    legal_entity_code: str
    role: AdvisorCockpitOwnerRole
    capabilities: frozenset[str]
    principal_status: str
    authorized_advisor_id: str | None
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
        if self.authorized_advisor_id is not None:
            headers["X-Authorized-Advisor-Id"] = self.authorized_advisor_id
        if self.authorized_portfolio_id is not None:
            headers["X-Authorized-Portfolio-Id"] = self.authorized_portfolio_id
        return headers


class AdvisorCockpitAccessError(ValueError):
    def __init__(self, *, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def require_advisor_cockpit_caller_context(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    legal_entity_code: str | None,
    role: str | None,
    capabilities: str | None,
    principal_status: str | None,
    authorized_advisor_id: str | None,
    authorized_portfolio_id: str | None,
) -> AdvisorCockpitCallerContext:
    required = _required_fields(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        legal_entity_code=legal_entity_code,
        role=role,
        capabilities=capabilities,
        principal_status=principal_status,
    )
    return _context_from_fields(
        required,
        authorized_advisor_id=_clean(authorized_advisor_id),
        authorized_portfolio_id=_clean(authorized_portfolio_id),
    )


def _context_from_fields(
    required: dict[str, str],
    *,
    authorized_advisor_id: str | None,
    authorized_portfolio_id: str | None,
) -> AdvisorCockpitCallerContext:
    role = required["X-Role"].upper()
    principal_status = required["X-Principal-Status"].upper()
    capabilities = _identifier_set(required["X-Caller-Capabilities"])
    _validate_principal(role, principal_status, capabilities)
    _validate_identifiers(required, capabilities, authorized_advisor_id, authorized_portfolio_id)
    advisor_scope = _authorized_advisor_scope(
        role=role,
        actor_id=required["X-Actor-Id"],
        authorized_advisor_id=authorized_advisor_id,
    )
    return AdvisorCockpitCallerContext(
        actor_id=required["X-Actor-Id"],
        caller_application=required["X-Caller-Application"],
        tenant_id=required["X-Tenant-Id"],
        region=required["X-Region"],
        booking_center_code=required["X-Booking-Center-Code"],
        legal_entity_code=required["X-Legal-Entity-Code"].upper(),
        role=cast(AdvisorCockpitOwnerRole, role),
        capabilities=capabilities,
        principal_status=principal_status,
        authorized_advisor_id=advisor_scope,
        authorized_portfolio_id=authorized_portfolio_id,
    )


def _validate_principal(
    role: str,
    principal_status: str,
    capabilities: frozenset[str],
) -> None:
    if role not in _SUPPORTED_ROLES:
        raise _access_denied()
    if principal_status != "ACTIVE":
        raise AdvisorCockpitAccessError(
            code="advisor_cockpit_principal_invalid",
            message="Advisor Cockpit access requires an active authenticated principal.",
            status_code=401,
        )
    if not capabilities:
        raise _invalid_context()


def _validate_identifiers(
    required: dict[str, str],
    capabilities: frozenset[str],
    authorized_advisor_id: str | None,
    authorized_portfolio_id: str | None,
) -> None:
    identifiers = (
        required["X-Actor-Id"],
        required["X-Caller-Application"],
        required["X-Tenant-Id"],
        required["X-Region"],
        required["X-Booking-Center-Code"],
        required["X-Legal-Entity-Code"],
        *capabilities,
        *(value for value in (authorized_advisor_id, authorized_portfolio_id) if value),
    )
    if any(not _IDENTIFIER_PATTERN.fullmatch(value) for value in identifiers):
        raise _invalid_context()


def _authorized_advisor_scope(
    *,
    role: str,
    actor_id: str,
    authorized_advisor_id: str | None,
) -> str | None:
    if role != "ADVISOR":
        return authorized_advisor_id
    if authorized_advisor_id not in {None, actor_id}:
        raise _access_denied()
    return actor_id


def require_advisor_cockpit_capability(
    caller: AdvisorCockpitCallerContext,
    capability: str,
) -> None:
    if capability not in caller.capabilities:
        raise _access_denied()


def require_advisor_cockpit_portfolio_scope(
    caller: AdvisorCockpitCallerContext,
    portfolio_id: str | None,
    *,
    required: bool = False,
) -> str | None:
    requested_portfolio_id = _clean(portfolio_id)
    entitled_portfolio_id = caller.authorized_portfolio_id
    if required and requested_portfolio_id is None:
        raise AdvisorCockpitAccessError(
            code="advisor_cockpit_portfolio_required",
            message="A portfolio is required for this advisor workflow.",
            status_code=422,
        )
    if requested_portfolio_id is not None and entitled_portfolio_id is None:
        raise AdvisorCockpitAccessError(
            code="advisor_cockpit_portfolio_scope_required",
            message="Trusted portfolio entitlement is required for this advisor workflow.",
            status_code=401,
        )
    if requested_portfolio_id is not None and requested_portfolio_id != entitled_portfolio_id:
        raise AdvisorCockpitAccessError(
            code="advisor_cockpit_portfolio_access_denied",
            message="Advisor Cockpit access is not available for this portfolio.",
            status_code=403,
        )
    return requested_portfolio_id or entitled_portfolio_id


def _required_fields(**values: str | None) -> dict[str, str]:
    headers = {
        "X-Actor-Id": _clean(values["actor_id"]),
        "X-Caller-Application": _clean(values["caller_application"]),
        "X-Tenant-Id": _clean(values["tenant_id"]),
        "X-Region": _clean(values["region"]),
        "X-Booking-Center-Code": _clean(values["booking_center_code"]),
        "X-Legal-Entity-Code": _clean(values["legal_entity_code"]),
        "X-Role": _clean(values["role"]),
        "X-Caller-Capabilities": _clean(values["capabilities"]),
        "X-Principal-Status": _clean(values["principal_status"]),
    }
    missing = [name for name, value in headers.items() if value is None]
    if missing:
        raise AdvisorCockpitAccessError(
            code="advisor_cockpit_caller_context_missing",
            message="Required Advisor Cockpit caller context is missing.",
            status_code=400,
        )
    return {name: value for name, value in headers.items() if value is not None}


def _identifier_set(value: str) -> frozenset[str]:
    return frozenset(part.strip() for part in value.split(",") if part.strip())


def _invalid_context() -> AdvisorCockpitAccessError:
    return AdvisorCockpitAccessError(
        code="advisor_cockpit_caller_context_invalid",
        message="Advisor Cockpit caller context is invalid.",
        status_code=400,
    )


def _access_denied() -> AdvisorCockpitAccessError:
    return AdvisorCockpitAccessError(
        code="advisor_cockpit_access_denied",
        message="Advisor Cockpit access is not available for this caller.",
        status_code=403,
    )


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
