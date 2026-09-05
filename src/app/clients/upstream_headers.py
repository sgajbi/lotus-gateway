from app.middleware.caller_identity import propagated_caller_identity
from app.middleware.correlation import propagation_headers


def build_upstream_headers(
    correlation_id: str,
    *,
    extras: dict[str, str] | None = None,
    caller_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    headers = propagation_headers(correlation_id)
    # Upstream Lotus services fence requests by the caller's presented identity
    # (lotus-core rejects any protected call without X-Tenant-Id). Propagate the
    # identity headers the caller presented for this request verbatim; a route's
    # explicitly admitted caller_headers always win over the ambient capture.
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
