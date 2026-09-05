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
from app.services.intake_access_policy import require_intake_write_capability


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


def intake_write_caller_context_dependency(
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
    capabilities: Annotated[str | None, Header(alias="X-Caller-Capabilities")] = None,
) -> dict[str, str]:
    """Admission for Core-mutating intake routes: the trusted context trio plus
    the governed intake write capability claim, refused before any upstream
    call otherwise. Tenant-authority verification itself is owned by lotus-core
    on its ingress; Gateway forwards only what this admission returned."""

    # Context first so callers missing headers get the actionable
    # missing_headers diagnostic (400) before the capability verdict (403).
    admitted = require_trusted_caller_context(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
    require_intake_write_capability(capabilities)
    return admitted


IntakeWriteCallerContext = Annotated[
    dict[str, str], Depends(intake_write_caller_context_dependency)
]
