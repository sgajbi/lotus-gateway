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
        "X-Actor-Id": actor_id.strip() if actor_id else actor_id,
        "X-Caller-Application": caller_application or "lotus-gateway",
        "X-Tenant-Id": tenant_id.strip() if tenant_id else tenant_id,
        "X-Region": region.strip() if region else region,
        "X-Booking-Center-Code": booking_center_code,
        "X-Role": role,
    }
    return {key: value for key, value in values.items() if value}
