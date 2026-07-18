import re
from dataclasses import dataclass

ADVISOR_BOOK_READ_CAPABILITY = "advisor.book.read"
ADVISOR_BOOK_ROLES = frozenset({"ADVISOR", "RELATIONSHIP_MANAGER", "PORTFOLIO_MANAGER"})
_ACTOR_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


@dataclass(frozen=True)
class AdvisorBookCallerContext:
    portfolio_manager_id: str
    tenant_id: str
    region: str
    booking_center_code: str
    role: str
    caller_application: str


class AdvisorBookCallerContextError(ValueError):
    def __init__(self, *, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def require_advisor_book_caller_context(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
    capabilities: str | None,
) -> AdvisorBookCallerContext:
    cleaned = _required_caller_fields(
        actor_id=actor_id,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
        capabilities=capabilities,
    )
    resolved_actor_id = cleaned["X-Actor-Id"]
    resolved_role = cleaned["X-Role"]
    _validate_actor_id(resolved_actor_id)
    _validate_access(role=resolved_role, capabilities=cleaned["X-Caller-Capabilities"])
    return AdvisorBookCallerContext(
        portfolio_manager_id=resolved_actor_id,
        tenant_id=cleaned["X-Tenant-Id"],
        region=cleaned["X-Region"],
        booking_center_code=cleaned["X-Booking-Center-Code"],
        role=resolved_role,
        caller_application=_clean(caller_application) or "lotus-gateway",
    )


def _required_caller_fields(
    *,
    actor_id: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
    capabilities: str | None,
) -> dict[str, str]:
    fields = {
        "X-Actor-Id": _clean(actor_id),
        "X-Tenant-Id": _clean(tenant_id),
        "X-Region": _clean(region),
        "X-Booking-Center-Code": _clean(booking_center_code),
        "X-Role": _clean(role),
        "X-Caller-Capabilities": _clean(capabilities),
    }
    missing = [name for name, value in fields.items() if value is None]
    if missing:
        raise AdvisorBookCallerContextError(
            code="advisor_book_caller_context_missing",
            message="Required advisor-book caller context is missing.",
            status_code=400,
        )
    return {name: value for name, value in fields.items() if value is not None}


def _validate_actor_id(actor_id: str) -> None:
    if not _ACTOR_ID_PATTERN.fullmatch(actor_id):
        raise AdvisorBookCallerContextError(
            code="advisor_book_caller_context_invalid",
            message="Advisor-book caller identity is invalid.",
            status_code=400,
        )


def _validate_access(*, role: str, capabilities: str) -> None:
    if role not in ADVISOR_BOOK_ROLES or ADVISOR_BOOK_READ_CAPABILITY not in _capability_set(
        capabilities
    ):
        raise AdvisorBookCallerContextError(
            code="advisor_book_access_denied",
            message="Advisor-book access is not available for this caller.",
            status_code=403,
        )


def _capability_set(value: str) -> frozenset[str]:
    return frozenset(part.strip() for part in value.split(",") if part.strip())


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
