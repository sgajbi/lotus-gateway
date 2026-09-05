"""Request-scoped propagation of the caller-presented tenant fence.

lotus-core's fail-closed ingress rejects any protected call without
X-Tenant-Id, and Gateway's composed reads must carry the tenant the caller
presented. The tenant is fencing context: forwarding it can only narrow what a
source returns. It is therefore the ONLY header this ambient mechanism
propagates, and only the Core-bound header builder consumes it: other
upstream boundaries (for example the DPM/Manage read-authority forwarding)
classify X-Tenant-Id itself as trusted authority.

Authority-bearing identity (X-Actor-Id, X-Role, X-Caller-Application, booking
centre, entitlement claims, credentials) never propagates ambiently: several
upstream boundaries treat those headers as Gateway-vetted authority (for
example the DPM/Manage read-authority forwarding), so an ambient merge would
turn unvalidated request headers into upstream authority on routes that never
admitted them. Routes forward authority only through their explicitly admitted
caller_headers, exactly as before. Gateway never mints, rewrites, or defaults
a tenant: a request that presented none propagates none.
"""

from collections.abc import Mapping
from contextvars import ContextVar, Token

CALLER_TENANT_HEADER = "X-Tenant-Id"

_caller_tenant_var: ContextVar[str] = ContextVar("caller_tenant", default="")


def capture_caller_identity(headers: Mapping[str, str]) -> Token:
    """Record the tenant fence the caller presented for this request."""

    return _caller_tenant_var.set((headers.get(CALLER_TENANT_HEADER) or "").strip())


def release_caller_identity(token: Token) -> None:
    _caller_tenant_var.reset(token)


def propagated_caller_identity() -> dict[str, str]:
    """The caller-presented tenant fence to carry on upstream requests."""

    tenant = _caller_tenant_var.get()
    return {CALLER_TENANT_HEADER: tenant} if tenant else {}


def admit_caller_tenant(tenant: str) -> Token:
    """Route-boundary re-admission of the tenant fence.

    A route that resolves its tenant scope through its own contract (for
    example an explicit query selector) binds the resolved value here so the
    ambient fence and the route's admitted scope are the same single tenant on
    every upstream call it makes."""

    return _caller_tenant_var.set(tenant.strip())
