from app.middleware.caller_identity import propagated_caller_identity
from app.middleware.correlation import propagation_headers


def build_upstream_headers(
    correlation_id: str,
    *,
    extras: dict[str, str] | None = None,
    caller_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    headers = propagation_headers(correlation_id)
    if extras:
        headers.update(extras)
    if caller_headers:
        headers.update(caller_headers)
    return headers


def build_core_upstream_headers(
    correlation_id: str,
    *,
    extras: dict[str, str] | None = None,
    caller_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    """Headers for lotus-core-bound calls only.

    Core's fail-closed ingress rejects any protected call without X-Tenant-Id,
    so Core-bound calls carry the caller-presented tenant fence captured at the
    request boundary. This stays OFF the generic builder deliberately: other
    upstream boundaries (for example the DPM/Manage read-authority forwarding)
    classify X-Tenant-Id as trusted authority, and an ambient merge there would
    turn an unadmitted request header into upstream scope. A route's explicitly
    admitted caller_headers always win over the ambient tenant."""

    headers = propagation_headers(correlation_id)
    headers.update(propagated_caller_identity())
    if extras:
        headers.update(extras)
    if caller_headers:
        headers.update(caller_headers)
    return headers


def build_idempotent_upstream_headers(
    correlation_id: str,
    idempotency_key: str,
    *,
    caller_headers: dict[str, str] | None = None,
    idempotency_header: str = "Idempotency-Key",
) -> dict[str, str]:
    return build_upstream_headers(
        correlation_id,
        extras={idempotency_header: idempotency_key},
        caller_headers=caller_headers,
    )


def build_archive_caller_headers(
    *,
    correlation_id: str,
    caller_headers: dict[str, str],
) -> dict[str, str]:
    headers = build_upstream_headers(
        correlation_id,
        extras={
            "X-Caller-Service": "lotus-gateway",
            "X-Actor-Type": caller_headers.get("X-Role", "user"),
            "X-Actor-Id": caller_headers["X-Actor-Id"],
            "X-Tenant-Id": caller_headers["X-Tenant-Id"],
            "X-Region": caller_headers["X-Region"],
        },
    )
    if booking_center_code := caller_headers.get("X-Booking-Center-Code"):
        headers["X-Booking-Center-Code"] = booking_center_code
    return headers
