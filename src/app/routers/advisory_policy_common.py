from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, Path
from fastapi.responses import JSONResponse

from app.contracts.advisory_policy import (
    AdvisoryPolicyEnvelopeResponse,
    AdvisoryPolicyErrorResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_policy_access_policy import (
    AdvisoryPolicyCallerContext,
    AdvisoryPolicyCallerContextError,
    AdvisoryPolicyOperation,
    require_advisory_policy_caller_context,
)

POLICY_VERSION_PATH = Path(
    ...,
    description="Policy pack version identifier owned by lotus-advise.",
)

_CALLER_CONTEXT_DESCRIPTION = (
    "Trusted caller context. Advisory-policy writes execute under the caller's own tenant, "
    "legal entity and actor identity; Gateway forwards them unchanged and never substitutes "
    "its own."
)

CALLER_CONTEXT_RESPONSES: dict[int | str, dict[str, object]] = {
    400: {
        "model": AdvisoryPolicyErrorResponse,
        "description": "Required advisory-policy caller context is missing or malformed.",
    },
    403: {
        "model": AdvisoryPolicyErrorResponse,
        "description": (
            "The caller's role and capabilities do not cover this advisory-policy operation. "
            "No request is made to lotus-advise."
        ),
    },
}


@dataclass(frozen=True)
class AdvisoryPolicyCallerHeaders:
    actor_id: str | None
    tenant_id: str | None
    legal_entity_code: str | None
    role: str | None
    capabilities: str | None


def advisory_policy_caller_headers(
    actor_id: Annotated[
        str | None, Header(alias="X-Actor-Id", description=_CALLER_CONTEXT_DESCRIPTION)
    ] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    legal_entity_code: Annotated[str | None, Header(alias="X-Legal-Entity-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
    capabilities: Annotated[str | None, Header(alias="X-Caller-Capabilities")] = None,
) -> AdvisoryPolicyCallerHeaders:
    return AdvisoryPolicyCallerHeaders(
        actor_id=actor_id,
        tenant_id=tenant_id,
        legal_entity_code=legal_entity_code,
        role=role,
        capabilities=capabilities,
    )


# The dependency and the return type, named once. Seven routes were each
# re-deriving `Annotated[AdvisoryPolicyCallerHeaders, Depends(...)]` and
# `... | JSONResponse`, which is four identical import lines and two identical
# annotations per file -- enough for the duplicate-code detector to see the
# import blocks themselves as clones. One canonical alias is both less code and
# one place to change when platform#775 replaces trusted headers.
AdmittedCallerHeaders = Annotated[
    AdvisoryPolicyCallerHeaders, Depends(advisory_policy_caller_headers)
]
AdvisoryPolicyRouteResponse = AdvisoryPolicyEnvelopeResponse | JSONResponse


def admit_advisory_policy_caller(
    *,
    operation: AdvisoryPolicyOperation,
    caller_headers: AdvisoryPolicyCallerHeaders,
) -> AdvisoryPolicyCallerContext:
    """Admit the caller for `operation`, raising before the route performs any I/O."""
    return require_advisory_policy_caller_context(
        operation=operation,
        actor_id=caller_headers.actor_id,
        tenant_id=caller_headers.tenant_id,
        legal_entity_code=caller_headers.legal_entity_code,
        role=caller_headers.role,
        capabilities=caller_headers.capabilities,
    )


async def admitted_policy_write(
    *,
    operation: AdvisoryPolicyOperation,
    caller_headers: AdvisoryPolicyCallerHeaders,
    call: Callable[[AdvisoryPolicyCallerContext, str], Awaitable[AdvisoryPolicyEnvelopeResponse]],
) -> AdvisoryPolicyEnvelopeResponse | JSONResponse:
    """Admit, refuse, or perform one advisory-policy write.

    Seven routes need exactly this sequence, and writing it seven times is how one
    of them eventually gets it subtly wrong -- refusing after the upstream call,
    or losing the correlation id that the refusal is reported under. The
    duplicate-code ratchet caught the first four copies of it, which is the gate
    working: the repair it forced is better than the code it rejected.

    `call` receives the admitted caller and the correlation id, so a route
    supplies only what is specific to it.
    """
    correlation_id = correlation_id_var.get()
    try:
        caller = admit_advisory_policy_caller(operation=operation, caller_headers=caller_headers)
    except AdvisoryPolicyCallerContextError as exc:
        return advisory_policy_error_response(error=exc, correlation_id=correlation_id)
    return await call(caller, correlation_id)


def advisory_policy_error_response(
    *, error: AdvisoryPolicyCallerContextError, correlation_id: str
) -> JSONResponse:
    payload = AdvisoryPolicyErrorResponse(
        code=error.code,
        message=error.message,
        correlation_id=correlation_id,
    )
    return JSONResponse(status_code=error.status_code, content=payload.model_dump(mode="json"))
