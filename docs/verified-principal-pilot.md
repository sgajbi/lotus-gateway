# Verified principal pilot

Gateway #834 adopts Platform's principal-resolution v3 and principal-credential wire semantics
on one existing operation:

`GET /api/v1/portfolio/portfolios/{portfolio_id}/positions/{security_id}/lots`

The deployment selects `PORTFOLIO_TAX_LOT_PRINCIPAL_POSTURE=verified`. The route verifies a compact
Ed25519 JWS with audience `lotus-gateway`, resolves tenant membership and `portfolio.read`, and
requires the exact requested portfolio in the effective grant scope. Delegated credentials require
the capability and portfolio in both the person's and application's grants. User and service
credentials require their own membership and grants without an application lookup.

This is finite consumer source capability. Other routes retain their existing admission. It does
not certify production identity, bank provisioning, a hosted grant store, composite membership,
downstream credential verification, or full Platform #775 completion. Core remains financial
authority; Gateway preserves its lot values, lineage and existing sanitized error mapping.

## Deployment wiring

The deployment composition root installs a `PrincipalGrantResolver` on
`application.state.principal_grant_resolver` before serving requests. The app-owned
`SignedPrincipalGrantResolver` takes a configured issuer, immutable trusted public-key map,
`GrantStore` and `RevocationStore`. These async ports belong to platform identity governance and
bank security authority; they do not query Core financial relationships for IAM membership.
The production clock defaults to system time. A missing resolver, issuer, trusted keys, membership,
grant or revocation provider remains unavailable. `AuthorityUnavailable` from any lookup maps to
503 `grant_store_unavailable`, never an empty permission set. Providers must raise that typed
exception for unreachable, stale beyond policy, or otherwise unanswerable authority.

Illustrative internal composition (authority adapters must be supplied by the designated operator):

```python
from app.services.principal_authority.resolver import SignedPrincipalGrantResolver

application.state.principal_grant_resolver = SignedPrincipalGrantResolver(
    issuer=configured_issuer,
    trusted_keys=trusted_ed25519_public_keys,
    grants=authoritative_grant_adapter,
    revocations=authoritative_revocation_adapter,
)
```

No adapter or persistent hosting service is shipped in this pilot. The smallest future boundary
proposal is to retain these ports and designate the existing identity deployment/operator that
owns tenant memberships, user grants, application grants and revocation freshness. Gateway needs
no financial tables or new service. Persistent hosting requires separate Platform ownership and
operator agreement; do not infer designation from this interface.

`header-trust` is the default for compatibility in `ENVIRONMENT=local` or `dev` only. In other
environments it refuses the pilot operation with 503. An unknown posture also refuses. A request
cannot select posture. Verified mode never falls back, and fixture public keys must never be
installed as deployment trust.

## Caller example and refusals

External request shape (the placeholder is an operator-issued credential, not a usable token):

```http
GET /api/v1/portfolio/portfolios/PF_1001/positions/US0378331005/lots
Authorization: Bearer <operator-issued-compact-JWS>
X-Correlation-Id: corr-tax-lots
```

Identity/capability headers do not contribute authority, even when they name another tenant or
an administrator. The verified tenant temporarily replaces the request's Core read fence and is
released on success or failure. No region, legal entity, booking centre or role is inferred, and
the credential is not forwarded to Core. Core receives the resolved tenant fence plus correlation
headers; this is Gateway enforcement, not cryptographic downstream principal adoption.

Denials expose only `{"detail":{"code":"<denial_class>"}}`: 401 for missing/malformed/expired,
wrong issuer/audience, unknown key, revoked or present-but-unverified credentials; 403 for tenant
non-membership, missing capability, portfolio outside scope or a delegated capability not held by
the user; 503 when authority is unavailable. No missing capability or resource-existence details
are returned. Signature verification precedes trusting payload claims. Expiry is exclusive; a
credential is refused at its exact expiry instant. Unknown algorithms, critical JWS extensions,
duplicate JSON members and ambiguous Authorization headers are refused.

## Proof and limitations

From the `lotus-gateway` checkout, on PowerShell or Bash:

```text
python -m pytest tests/integration/test_portfolio_principal.py -q
make lint
make typecheck
```

The registered-route proof uses generated Ed25519 keys and signed bytes, controlled membership,
grants and revocation, the real PortfolioService/Core client, and substituted Core HTTP transport.
It measures zero protected Core calls for all 13 denial classes, proves a foreign signature only
admits when its matching public key is explicitly trusted, and checks source lot fidelity,
delegated intersections and simultaneous tenant isolation. It does not provision or certify bank
identity, live Core access or a persistent grant store. No runtime topology split is introduced.
