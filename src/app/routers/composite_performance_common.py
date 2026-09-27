from app.routers.workbench_caller_context import (
    WORKBENCH_CALLER_OPENAPI,
    UnambiguousWorkbenchCallerContext,
)

COMPOSITE_CALLER_OPENAPI = WORKBENCH_CALLER_OPENAPI
CompositeCallerContext = UnambiguousWorkbenchCallerContext


def composite_caller_context(caller_headers: dict[str, str]) -> dict[str, str | None]:
    """Map request-admitted transport headers into the application context."""
    return {
        "actor_id": caller_headers.get("X-Actor-Id"),
        "caller_application": caller_headers.get("X-Caller-Application"),
        "tenant_id": caller_headers.get("X-Tenant-Id"),
        "region": caller_headers.get("X-Region"),
        "booking_center_code": caller_headers.get("X-Booking-Center-Code"),
        "role": caller_headers.get("X-Role"),
    }
