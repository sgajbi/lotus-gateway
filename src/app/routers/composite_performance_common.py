def composite_caller_context(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> dict[str, str | None]:
    return {
        "actor_id": actor_id,
        "caller_application": caller_application,
        "tenant_id": tenant_id,
        "region": region,
        "booking_center_code": booking_center_code,
        "role": role,
    }
