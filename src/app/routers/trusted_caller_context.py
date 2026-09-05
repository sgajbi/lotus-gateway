"""Shared trusted caller-context admission for routes that forward it upstream.

One owner for the Header-dependency shape: a route that must carry the
caller's admitted identity on upstream calls declares this dependency, which
fails closed (400 `missing_caller_context`) when the required trio —
X-Actor-Id, X-Tenant-Id, X-Region — is absent. Core writes especially must
carry an explicitly admitted tenant: Core's fail-closed ingress refuses
tenant-less protected calls, and a caller-presented header must never scope a
mutation without passing this admission first.
"""

from typing import Annotated

from fastapi import Depends, Header

from app.services.caller_context import caller_context_headers


def require_trusted_caller_context(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> dict[str, str]:
    return caller_context_headers(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )


def trusted_caller_context_dependency(
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> dict[str, str]:
    return require_trusted_caller_context(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )


TrustedCallerContext = Annotated[dict[str, str], Depends(trusted_caller_context_dependency)]
