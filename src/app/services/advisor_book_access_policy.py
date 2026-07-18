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
    cleaned = {
        "X-Actor-Id": _clean(actor_id),
        "X-Tenant-Id": _clean(tenant_id),
        "X-Region": _clean(region),
        "X-Booking-Center-Code": _clean(booking_center_code),
        "X-Role": _clean(role),
        "X-Caller-Capabilities": _clean(capabilities),
    }
    missing = [name for name, value in cleaned.items() if value is None]
    if missing:
        raise AdvisorBookCallerContextError(
            code="advisor_book_caller_context_missing",
            message="Required advisor-book caller context is missing.",
            status_code=400,
        )

    resolved_actor_id = cleaned["X-Actor-Id"] or ""
    if not _ACTOR_ID_PATTERN.fullmatch(resolved_actor_id):
        raise AdvisorBookCallerContextError(
            code="advisor_book_caller_context_invalid",
            message="Advisor-book caller identity is invalid.",
            status_code=400,
        )

    resolved_role = cleaned["X-Role"] or ""
    resolved_capabilities = _capability_set(cleaned["X-Caller-Capabilities"] or "")
    if (
        resolved_role not in ADVISOR_BOOK_ROLES
        or ADVISOR_BOOK_READ_CAPABILITY not in resolved_capabilities
    ):
        raise AdvisorBookCallerContextError(
            code="advisor_book_access_denied",
            message="Advisor-book access is not available for this caller.",
            status_code=403,
        )

    return AdvisorBookCallerContext(
        portfolio_manager_id=resolved_actor_id,
        tenant_id=cleaned["X-Tenant-Id"] or "",
        region=cleaned["X-Region"] or "",
        booking_center_code=cleaned["X-Booking-Center-Code"] or "",
        role=resolved_role,
        caller_application=_clean(caller_application) or "lotus-gateway",
    )


def _capability_set(value: str) -> frozenset[str]:
    return frozenset(part.strip() for part in value.split(",") if part.strip())


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
