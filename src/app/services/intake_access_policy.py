"""Access policy for intake write routes.

Gateway's trust design derives caller identity from trusted server-side
context headers; it does not authenticate principals (the platform's verified
service-credential contract is adopted per upstream as environments promote,
and lotus-core owns tenant-authority enforcement on its own ingress). Within
that design, a Core-mutating route must still demand more than reachable
transport: the caller has to present the governed intake write capability
claim, mirroring every other Gateway write family. A caller without the claim
is refused before any upstream call.
"""

from fastapi import HTTPException, status

INTAKE_WRITE_CAPABILITY = "core.intake.write"


def require_intake_write_capability(capabilities: str | None) -> None:
    presented = {part.strip() for part in (capabilities or "").split(",") if part.strip()}
    if INTAKE_WRITE_CAPABILITY not in presented:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "intake_write_capability_required",
                "message": (
                    "Intake writes require the governed core.intake.write capability claim."
                ),
            },
        )
