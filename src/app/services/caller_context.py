from fastapi import HTTPException, status


def caller_context_headers(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> dict[str, str]:
    missing = [
        name
        for name, value in {
            "X-Actor-Id": actor_id,
            "X-Tenant-Id": tenant_id,
            "X-Region": region,
        }.items()
        if not value or not value.strip()
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "missing_caller_context",
                "message": "Required caller context headers are missing.",
                "missing_headers": missing,
            },
        )
    values = {
        "X-Actor-Id": _clean_header_value(actor_id),
        "X-Caller-Application": _clean_header_value(caller_application) or "lotus-gateway",
        "X-Tenant-Id": _clean_header_value(tenant_id),
        "X-Region": _clean_header_value(region),
        "X-Booking-Center-Code": _clean_header_value(booking_center_code),
        "X-Role": _clean_header_value(role),
    }
    return {key: value for key, value in values.items() if value}


def _clean_header_value(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
