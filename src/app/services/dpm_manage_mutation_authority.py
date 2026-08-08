from __future__ import annotations

import re
from collections.abc import AsyncIterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Annotated, Iterator

from fastapi import Header, HTTPException, status

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_GATEWAY_SERVICE_IDENTITY = "lotus-gateway"
_MANAGE_WRITE_CAPABILITY = "manage.write"
_AUTHORITY_HEADER_NAMES = frozenset(
    {
        "x-actor-id",
        "x-tenant-id",
        "x-region",
        "x-role",
        "x-service-identity",
        "x-capabilities",
    }
)


@dataclass(frozen=True, slots=True)
class DpmManageMutationAuthority:
    """Trusted caller audit identity plus Gateway-owned Manage write authority."""

    actor_id: str
    tenant_id: str
    role: str
    region: str | None = None

    def upstream_headers(self) -> dict[str, str]:
        headers = {
            "X-Actor-Id": self.actor_id,
            "X-Tenant-Id": self.tenant_id,
            "X-Role": self.role,
            "X-Service-Identity": _GATEWAY_SERVICE_IDENTITY,
            "X-Capabilities": _MANAGE_WRITE_CAPABILITY,
        }
        if self.region is not None:
            headers["X-Region"] = self.region
        return headers


class DpmManageMutationAuthorityError(RuntimeError):
    """Fail closed when a Manage mutation escapes its request authority boundary."""


_authority_var: ContextVar[DpmManageMutationAuthority | None] = ContextVar(
    "dpm_manage_mutation_authority",
    default=None,
)


def build_dpm_manage_mutation_authority(
    *,
    actor_id: str | None,
    tenant_id: str | None,
    role: str | None,
    region: str | None,
) -> DpmManageMutationAuthority:
    cleaned_actor_id = _clean(actor_id)
    cleaned_tenant_id = _clean(tenant_id)
    cleaned_role = _clean(role)
    if cleaned_actor_id is None or cleaned_tenant_id is None or cleaned_role is None:
        raise _caller_context_error(
            code="dpm_mutation_caller_context_missing",
            message="A governed caller identity is required for this DPM action.",
        )

    cleaned_region = _clean(region)
    values = [cleaned_actor_id, cleaned_tenant_id, cleaned_role]
    if cleaned_region is not None:
        values.append(cleaned_region)
    if any(not _IDENTIFIER_PATTERN.fullmatch(value) for value in values):
        raise _caller_context_error(
            code="dpm_mutation_caller_context_invalid",
            message="The DPM action caller identity is invalid.",
        )

    return DpmManageMutationAuthority(
        actor_id=cleaned_actor_id,
        tenant_id=cleaned_tenant_id,
        role=cleaned_role,
        region=cleaned_region,
    )


async def bind_dpm_manage_mutation_authority(
    actor_id: Annotated[
        str | None,
        Header(
            alias="X-Actor-Id",
            description="Authenticated actor required for a DPM mutation.",
        ),
    ] = None,
    tenant_id: Annotated[
        str | None,
        Header(
            alias="X-Tenant-Id",
            description="Authenticated tenant required for a DPM mutation.",
        ),
    ] = None,
    role: Annotated[
        str | None,
        Header(
            alias="X-Role",
            description="Authenticated business role required for a DPM mutation.",
        ),
    ] = None,
    region: Annotated[
        str | None,
        Header(
            alias="X-Region",
            description="Authenticated operating region when available.",
        ),
    ] = None,
) -> AsyncIterator[None]:
    """Bind derived Manage authority for a registered DPM mutation route."""

    authority = build_dpm_manage_mutation_authority(
        actor_id=actor_id,
        tenant_id=tenant_id,
        role=role,
        region=region,
    )
    token = _authority_var.set(authority)
    try:
        yield
    finally:
        _authority_var.reset(token)


def authorize_dpm_manage_mutation_headers(
    headers: dict[str, str],
) -> dict[str, str]:
    """Replace caller-supplied workload authority with the Gateway-owned contract."""

    resolved_authority = _authority_var.get()
    if resolved_authority is None:
        raise DpmManageMutationAuthorityError(
            "DPM Manage mutation authority is unavailable for this request."
        )
    authorized = {
        name: value
        for name, value in headers.items()
        if name.lower() not in _AUTHORITY_HEADER_NAMES
    }
    authorized.update(resolved_authority.upstream_headers())
    return authorized


@contextmanager
def dpm_manage_mutation_authority_scope(
    authority: DpmManageMutationAuthority,
) -> Iterator[None]:
    """Provide an explicit scope for client-level contract tests and non-HTTP callers."""

    token: Token[DpmManageMutationAuthority | None] = _authority_var.set(authority)
    try:
        yield
    finally:
        _authority_var.reset(token)


def _caller_context_error(*, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": code, "message": message},
    )


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
