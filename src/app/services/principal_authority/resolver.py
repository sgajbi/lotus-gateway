"""Resolve signed identity through authoritative membership, revocation and grants."""

import time
from collections.abc import Callable, Mapping
from types import MappingProxyType

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.services.principal_authority.contracts import (
    AuthorityUnavailable,
    GrantStore,
    PrincipalDenied,
    ResolvedPrincipal,
    RevocationStore,
)
from app.services.principal_authority.credential import VerifiedCredential, verify_credential


class SignedPrincipalGrantResolver:
    def __init__(
        self,
        *,
        issuer: str,
        trusted_keys: Mapping[str, Ed25519PublicKey],
        grants: GrantStore | None,
        revocations: RevocationStore | None,
        clock: Callable[[], float] = time.time,
    ):
        self._issuer = issuer
        self._keys = MappingProxyType(dict(trusted_keys))
        self._grants = grants
        self._revocations = revocations
        self._clock = clock

    async def resolve(
        self,
        credential: str,
        *,
        required_capabilities: frozenset[str],
        requested_portfolios: frozenset[str],
    ) -> ResolvedPrincipal:
        if not self._issuer or not self._keys:
            raise PrincipalDenied("grant_store_unavailable", 503)
        verified = verify_credential(
            credential,
            trusted_keys=self._keys,
            issuer=self._issuer,
            audience="lotus-gateway",
            now=self._clock(),
        )
        try:
            return await self._resolve_grants(verified, required_capabilities, requested_portfolios)
        except AuthorityUnavailable:
            raise PrincipalDenied("grant_store_unavailable", 503) from None

    async def _resolve_grants(
        self,
        principal: VerifiedCredential,
        required: frozenset[str],
        requested: frozenset[str],
    ) -> ResolvedPrincipal:
        if self._revocations is None or self._grants is None:
            raise AuthorityUnavailable
        if await self._revocations.is_revoked(principal.credential_id, principal.subject):
            raise PrincipalDenied("revoked_principal", 401)
        if not await self._grants.tenant_members(principal.subject, principal.tenant_id):
            raise PrincipalDenied("tenant_not_a_member", 403)
        user = await self._grants.grants_for(principal.subject, principal.tenant_id)
        capabilities, scope = user.capabilities, user.portfolio_scope
        if principal.delegated_actor is not None:
            application = await self._grants.application_grants_for(
                principal.delegated_actor, principal.tenant_id
            )
            if required <= application.capabilities and not required <= capabilities:
                raise PrincipalDenied("delegated_capability_not_held_by_user", 403)
            capabilities = capabilities & application.capabilities
            scope = scope & application.portfolio_scope
        if not required <= capabilities:
            raise PrincipalDenied("capability_not_granted", 403)
        if not requested <= scope:
            raise PrincipalDenied("portfolio_outside_scope", 403)
        return ResolvedPrincipal(
            principal.principal_kind,
            principal.subject,
            principal.tenant_id,
            capabilities,
            scope,
            principal.delegated_actor,
            principal.credential_id,
        )
