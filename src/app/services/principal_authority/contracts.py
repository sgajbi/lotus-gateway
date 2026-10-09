"""Runtime ports for Platform's principal-resolution v3 contract."""

from dataclasses import dataclass
from typing import Literal, Protocol

PrincipalKind = Literal["user", "service", "delegated"]


class AuthorityUnavailable(Exception):
    """An authoritative lookup cannot answer; never treat this as an empty grant."""


class PrincipalDenied(Exception):
    """Safe denial class; contains no credential, entitlement or resource details."""

    def __init__(self, denial_class: str, status_code: int):
        self.denial_class = denial_class
        self.status_code = status_code
        super().__init__(denial_class)


@dataclass(frozen=True)
class GrantSet:
    capabilities: frozenset[str]
    portfolio_scope: frozenset[str]


@dataclass(frozen=True)
class ResolvedPrincipal:
    principal_kind: PrincipalKind
    subject: str
    tenant_id: str
    capabilities: frozenset[str]
    portfolio_scope: frozenset[str]
    delegated_actor: str | None
    credential_id: str


class GrantStore(Protocol):
    async def tenant_members(self, subject: str, tenant_id: str) -> bool: ...

    async def grants_for(self, subject: str, tenant_id: str) -> GrantSet: ...

    async def application_grants_for(self, actor: str, tenant_id: str) -> GrantSet: ...


class RevocationStore(Protocol):
    async def is_revoked(self, credential_id: str, subject: str) -> bool: ...


class PrincipalGrantResolver(Protocol):
    async def resolve(
        self,
        credential: str,
        *,
        required_capabilities: frozenset[str],
        requested_portfolios: frozenset[str],
    ) -> ResolvedPrincipal: ...
