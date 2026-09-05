"""Request-scoped propagation of the caller-presented identity headers.

Gateway is a trusted-context front door: callers present their identity as X-*
headers, each route admits what its contract requires, and every upstream Lotus
service enforces its own fencing over the same header vocabulary (lotus-core's
fail-closed tenant ingress rejects any protected call without X-Tenant-Id).
These contextvars carry the identity the caller presented so upstream calls
propagate the caller's scope verbatim — Gateway never mints, rewrites, or
defaults an identity, and a request that presented no identity propagates none.

Only the platform identity vocabulary is captured. Entitlement claims
(X-Caller-Capabilities, X-Authorized-*) and credentials (Authorization) are
deliberately excluded: routes that need them forward them explicitly under
their own contracts.
"""

from collections.abc import Mapping
from contextvars import ContextVar, Token

CALLER_IDENTITY_HEADER_NAMES: tuple[str, ...] = (
    "X-Tenant-Id",
    "X-Actor-Id",
    "X-Caller-Application",
    "X-Region",
    "X-Booking-Center-Code",
    "X-Role",
)

_caller_identity_var: ContextVar[tuple[tuple[str, str], ...]] = ContextVar(
    "caller_identity_headers", default=()
)


def capture_caller_identity(headers: Mapping[str, str]) -> Token:
    """Record the identity headers the caller presented for this request."""

    presented = tuple(
        (name, value)
        for name in CALLER_IDENTITY_HEADER_NAMES
        if (value := (headers.get(name) or "").strip())
    )
    return _caller_identity_var.set(presented)


def release_caller_identity(token: Token) -> None:
    _caller_identity_var.reset(token)


def propagated_caller_identity() -> dict[str, str]:
    """The caller-presented identity headers to carry on upstream requests."""

    return dict(_caller_identity_var.get())
