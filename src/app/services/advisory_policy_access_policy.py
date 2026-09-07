"""Advisory-policy writes must carry the caller's admitted scope, never Gateway's.

Every write on this path previously travelled under a module constant:
`X-Tenant-Id: tenant_sg_001` and `X-Legal-Entity-Code: REFERENCE`, with the role
and capability chosen by the calling code and the actor read out of the request
BODY behind a fallback such as `advisor_1`. The routes admitted nothing, so there
was no path by which a real caller's scope could reach the client.

That is the boundary rule inverted. Gateway propagates the scope it admitted; it
does not mint one. `tenant_sg_001` is a real seeded tenant rather than a neutral
control-plane identifier, so every policy write executed under that tenant's
identity whoever called it, and was indistinguishable downstream from that
tenant's own activity.

Three things follow, and they are separate:

* **Tenant, legal entity and actor are propagated.** They arrive as admitted
  caller context and are forwarded unchanged. Gateway has no opinion about them.
* **Role and capability are checked, not chosen.** These operations are delegated
  USER authority — an advisor creates an evaluation, a checker signs it off — so
  the caller presents a role and a capability set, and Gateway refuses unless
  they cover the operation being performed. Choosing them here would be minting
  under a different name.
* **Service identity stays Gateway's own.** `X-Service-Identity: lotus-gateway`
  is the one header in the old set that was true, because Gateway really is the
  service making the call. It says nothing about who authorised it.

The refusal happens before any outbound I/O. A caller without scope must not
reach lotus-advise at all, rather than being refused by it afterwards.

**This is not production authentication.** The headers are trusted at this
perimeter exactly as the Core-bound paths already trust them, and that is a
bounded development posture, not verified identity. Verified principal and
capability authority is lotus-platform#775; when it lands, this module is where
an admitted principal replaces a trusted header, and nothing downstream of it has
to change. Propagating what the caller presents is strictly better than asserting
a constant, and it is not the same as having authenticated them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Gateway is genuinely the service placing the call, so this one is a true
# statement about the transport rather than a claim about authority.
POLICY_CONTROL_SERVICE_IDENTITY = "lotus-gateway"

POLICY_STEWARD_ROLE = "POLICY_STEWARD"
POLICY_CHECKER_ROLE = "POLICY_CHECKER"
ADVISOR_ROLE = "ADVISOR"
COMPLIANCE_REVIEWER_ROLE = "COMPLIANCE_REVIEWER"

_ACTOR_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


@dataclass(frozen=True)
class AdvisoryPolicyOperation:
    """What a caller must hold to perform one advisory-policy write.

    Named per operation rather than per route so the requirement travels with the
    business act. Two routes performing the same act ask for the same scope, and
    a new route cannot invent a weaker one by omission.
    """

    name: str
    capability: str
    permitted_roles: frozenset[str]


POLICY_PACK_VALIDATE = AdvisoryPolicyOperation(
    name="policy_pack.validate",
    capability="advisory.policy_pack.validate",
    permitted_roles=frozenset({POLICY_STEWARD_ROLE}),
)
POLICY_PACK_ACTIVATE = AdvisoryPolicyOperation(
    name="policy_pack.activate",
    capability="advisory.policy_pack.activate",
    permitted_roles=frozenset({POLICY_CHECKER_ROLE}),
)
POLICY_EVALUATION_FINALIZE = AdvisoryPolicyOperation(
    name="policy_evaluation.finalize",
    capability="advisory.policy_evaluation.finalize",
    permitted_roles=frozenset({ADVISOR_ROLE}),
)
POLICY_EVALUATION_REVIEW_EVENT = AdvisoryPolicyOperation(
    name="policy_evaluation.review_event",
    capability="advisory.policy_evaluation.review_event",
    permitted_roles=frozenset({COMPLIANCE_REVIEWER_ROLE}),
)
POLICY_EVALUATION_SIGN_OFF = AdvisoryPolicyOperation(
    name="policy_evaluation.sign_off",
    capability="advisory.policy_evaluation.sign_off",
    permitted_roles=frozenset({POLICY_CHECKER_ROLE}),
)
POLICY_EVALUATION_REPORT_PACKAGE = AdvisoryPolicyOperation(
    name="policy_evaluation.report_package",
    capability="advisory.policy_evaluation.report_package",
    permitted_roles=frozenset({POLICY_CHECKER_ROLE}),
)
POLICY_EVALUATION_AI_EVIDENCE = AdvisoryPolicyOperation(
    name="policy_evaluation.ai_evidence",
    capability="advisory.policy_evaluation.ai_evidence",
    permitted_roles=frozenset({COMPLIANCE_REVIEWER_ROLE}),
)


@dataclass(frozen=True)
class AdvisoryPolicyCallerContext:
    """Scope admitted from the caller, for one specific operation.

    `capability` is the operation's capability, retained only after the caller
    was shown to hold it. Forwarding the single capability being exercised rather
    than the caller's whole set keeps the outbound claim as narrow as the act.
    """

    actor_id: str
    tenant_id: str
    legal_entity_code: str
    role: str
    capability: str


class AdvisoryPolicyCallerContextError(ValueError):
    def __init__(self, *, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def require_advisory_policy_caller_context(
    *,
    operation: AdvisoryPolicyOperation,
    actor_id: str | None,
    tenant_id: str | None,
    legal_entity_code: str | None,
    role: str | None,
    capabilities: str | None,
) -> AdvisoryPolicyCallerContext:
    """Admit the caller's scope for `operation`, or refuse before any I/O."""
    cleaned = _required_caller_fields(
        actor_id=actor_id,
        tenant_id=tenant_id,
        legal_entity_code=legal_entity_code,
        role=role,
        capabilities=capabilities,
    )
    _validate_shapes(cleaned)
    _validate_access(
        operation=operation,
        role=cleaned["X-Role"],
        capabilities=cleaned["X-Caller-Capabilities"],
    )
    return AdvisoryPolicyCallerContext(
        actor_id=cleaned["X-Actor-Id"],
        tenant_id=cleaned["X-Tenant-Id"],
        legal_entity_code=cleaned["X-Legal-Entity-Code"],
        role=cleaned["X-Role"],
        capability=operation.capability,
    )


def _required_caller_fields(
    *,
    actor_id: str | None,
    tenant_id: str | None,
    legal_entity_code: str | None,
    role: str | None,
    capabilities: str | None,
) -> dict[str, str]:
    fields = {
        "X-Actor-Id": _clean(actor_id),
        "X-Tenant-Id": _clean(tenant_id),
        "X-Legal-Entity-Code": _clean(legal_entity_code),
        "X-Role": _clean(role),
        "X-Caller-Capabilities": _clean(capabilities),
    }
    if any(value is None for value in fields.values()):
        # The missing names are deliberately not listed. Which field is absent is
        # not useful to a legitimate caller sending none of them, and it is a
        # probe oracle for one discovering the shape of the perimeter.
        raise AdvisoryPolicyCallerContextError(
            code="advisory_policy_caller_context_missing",
            message="Required advisory-policy caller context is missing.",
            status_code=400,
        )
    return {name: value for name, value in fields.items() if value is not None}


def _validate_shapes(cleaned: dict[str, str]) -> None:
    # Tenant and legal entity are validated as well as the actor, because these
    # travel outbound as authority. An unconstrained value would let a caller put
    # header-breaking or ambiguous text into a field lotus-advise reads as scope.
    if not _ACTOR_ID_PATTERN.fullmatch(cleaned["X-Actor-Id"]) or not all(
        _SCOPE_PATTERN.fullmatch(cleaned[name]) for name in ("X-Tenant-Id", "X-Legal-Entity-Code")
    ):
        raise AdvisoryPolicyCallerContextError(
            code="advisory_policy_caller_context_invalid",
            message="Advisory-policy caller context is invalid.",
            status_code=400,
        )


def _validate_access(
    *,
    operation: AdvisoryPolicyOperation,
    role: str,
    capabilities: str,
) -> None:
    if role not in operation.permitted_roles or operation.capability not in _capability_set(
        capabilities
    ):
        # One refusal for both, so the response cannot be used to enumerate which
        # roles or capabilities exist.
        raise AdvisoryPolicyCallerContextError(
            code="advisory_policy_access_denied",
            message="Advisory-policy access is not available for this caller.",
            status_code=403,
        )


def _capability_set(value: str) -> frozenset[str]:
    return frozenset(part.strip() for part in value.split(",") if part.strip())


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
