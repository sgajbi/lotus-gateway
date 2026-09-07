from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, Path
from fastapi.responses import JSONResponse

from app.contracts.advisory_policy import AdvisoryPolicyErrorResponse
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


def advisory_policy_error_response(
    *, error: AdvisoryPolicyCallerContextError, correlation_id: str
) -> JSONResponse:
    payload = AdvisoryPolicyErrorResponse(
        code=error.code,
        message=error.message,
        correlation_id=correlation_id,
    )
    return JSONResponse(status_code=error.status_code, content=payload.model_dump(mode="json"))
