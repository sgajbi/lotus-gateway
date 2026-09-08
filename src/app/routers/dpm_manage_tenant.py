"""The tenant every lotus-manage-bound route forwards, declared once.

`lotus-manage` requires a tenant on the mandate, monitoring, proof-pack,
outcome-review and wave aggregates and refuses a request that omits one
(`DPM_MANDATE_TENANT_REQUIRED`, 422). Gateway forwards the caller's **admitted**
tenant to those routes and never substitutes one of its own — the rule Gateway
#753 established when advisory-policy writes were sending a seeded tenant from a
module constant, so every write executed under one tenant's identity whoever
called it.

Declared as one annotated type rather than repeated per route because dozens of
routes forward it, and a route that spells the constraint slightly differently is
a route with a different contract.

No count is written here on purpose. This docstring said "23 call sites" while
the measured number was 54, which is the fourth stale enumeration found in this
family: #763 named 23 call sites, #770 found four more a commit later, #771
found twenty-two campaign operations whose requirement never reaches the served
OpenAPI. A number in prose is true of the revision it was taken from and of
nothing else. Where a count is load-bearing it is derived and asserted —
`test_manage_tenant_forwarding_population.py` walks the client classes, and
`test_campaign_tenant_documentation.py` derives the campaign figure the
documentation states.

**`pattern=r"\\S"`, not `min_length=1` alone.** Whitespace is a character, so a
length check admits `X-Tenant-Id: %20`. lotus-manage refuses that value — but it
refuses it *after* Gateway has made the call, which is the wrong side of the
boundary. Refusing here means an unusable tenant never reaches an upstream at
all. The pattern is deliberately unanchored: `^\\s*\\S.*$` would reject a trailing
newline that the upstream normaliser accepts, and a Gateway that refuses what
lotus-manage would have answered is worse than one that forwards it.

Padding is left to normalise upstream rather than being stripped here.
lotus-manage treats `" alpha"` and `"alpha"` as one tenant; stripping locally as
well would be a second normaliser that can drift from theirs, and two normalisers
disagreeing is how a tenant's own evidence gets partitioned.

`OptionalDpmManageTenantId` is the same header on routes whose *primary* answer
comes from somewhere else and where lotus-manage evidence is one composed part
of the response — the Workbench risk surfaces, where the risk measures are
lotus-risk-owned. Requiring the header there would break callers of a shipped
Workbench contract to fence a section of the payload they may not be asking for;
omitting it reports that one section unavailable and leaves the rest intact. It
is optional in what it admits, never in what it forwards: a tenant that is
present is forwarded unchanged, and one that is absent means no lotus-manage
call is made at all.

**This is a correctness boundary, not authentication.** The tenant is a
caller-asserted scope: it narrows what is read, and does not prove the caller is
entitled to that tenant. Verified principal authority is lotus-manage#624 and
lotus-platform#775; nothing here should be cited as providing it.
"""

from typing import Annotated

from fastapi import Header

MANAGE_TENANT_DESCRIPTION = (
    "Tenant whose lotus-manage evidence is being read or written. Required: mandate, "
    "monitoring, proof-pack, outcome-review and wave records are stored per tenant, and the "
    "same identifier may exist under more than one. Forwarded to lotus-manage unchanged; "
    "Gateway never substitutes a tenant of its own. Caller-asserted scope, not authenticated "
    "authority."
)

DpmManageTenantId = Annotated[
    str,
    Header(
        alias="X-Tenant-Id",
        pattern=r"\S",
        min_length=1,
        description=MANAGE_TENANT_DESCRIPTION,
        examples=["tenant-sg"],
    ),
]

OPTIONAL_MANAGE_TENANT_DESCRIPTION = (
    "Tenant whose lotus-manage mandate evidence should be composed into this response. "
    "Optional: the risk measures themselves are lotus-risk-owned and need no tenant, so a "
    "request that omits this header still returns them. The mandate comparison is then "
    "reported as unavailable with that reason, because lotus-manage stores mandate evidence "
    "per tenant and Gateway will not guess one. Caller-asserted scope, not authenticated "
    "authority."
)

OptionalDpmManageTenantId = Annotated[
    str | None,
    Header(
        alias="X-Tenant-Id",
        pattern=r"\S",
        min_length=1,
        description=OPTIONAL_MANAGE_TENANT_DESCRIPTION,
        examples=["tenant-sg"],
    ),
]
