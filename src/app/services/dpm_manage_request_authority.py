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
class DpmManageRequestAuthority:
    """Validated caller context and Gateway-owned Manage mutation authority."""

    actor_id: str
    tenant_id: str
    role: str
    region: str | None = None

    def caller_headers(self) -> dict[str, str]:
        headers = {
            "X-Actor-Id": self.actor_id,
            "X-Tenant-Id": self.tenant_id,
            "X-Role": self.role,
        }
        if self.region is not None:
            headers["X-Region"] = self.region
        return headers

    def mutation_headers(self) -> dict[str, str]:
        return {
            **self.caller_headers(),
            "X-Service-Identity": _GATEWAY_SERVICE_IDENTITY,
            "X-Capabilities": _MANAGE_WRITE_CAPABILITY,
        }


class DpmManageRequestAuthorityError(RuntimeError):
    """Fail closed when a Manage mutation escapes its request authority boundary."""


_authority_var: ContextVar[DpmManageRequestAuthority | None] = ContextVar(
    "dpm_manage_request_authority",
    default=None,
)


def build_dpm_manage_request_authority(
    *,
    actor_id: str | None,
    tenant_id: str | None,
    role: str | None,
    region: str | None,
) -> DpmManageRequestAuthority:
    cleaned_actor_id = _clean(actor_id)
    cleaned_tenant_id = _clean(tenant_id)
    cleaned_role = _clean(role)
    if cleaned_actor_id is None or cleaned_tenant_id is None or cleaned_role is None:
        raise _caller_context_error(
            code="dpm_caller_context_missing",
            message="A governed caller identity is required for this DPM workflow.",
        )

    cleaned_region = _clean(region)
    values = [cleaned_actor_id, cleaned_tenant_id, cleaned_role]
    if cleaned_region is not None:
        values.append(cleaned_region)
    if any(not _IDENTIFIER_PATTERN.fullmatch(value) for value in values):
        raise _caller_context_error(
            code="dpm_caller_context_invalid",
            message="The DPM workflow caller identity is invalid.",
        )

    return DpmManageRequestAuthority(
        actor_id=cleaned_actor_id,
        tenant_id=cleaned_tenant_id,
        role=cleaned_role,
        region=cleaned_region,
    )


async def bind_dpm_manage_request_authority(
    actor_id: Annotated[
        str | None,
        Header(
            alias="X-Actor-Id",
            description="Authenticated actor required for a governed DPM workflow.",
        ),
    ] = None,
    tenant_id: Annotated[
        str | None,
        Header(
            alias="X-Tenant-Id",
            description="Authenticated tenant required for a governed DPM workflow.",
        ),
    ] = None,
    role: Annotated[
        str | None,
        Header(
            alias="X-Role",
            description="Authenticated business role required for a governed DPM workflow.",
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
    """Bind validated caller context for one registered Gateway DPM route."""

    authority = build_dpm_manage_request_authority(
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


def forward_dpm_manage_read_headers(headers: dict[str, str]) -> dict[str, str]:
    """Forward validated caller context when a registered DPM read owns the request scope."""

    resolved_authority = _authority_var.get()
    if resolved_authority is None:
        return dict(headers)
    return _replace_authority_headers(headers, resolved_authority.caller_headers())


def authorize_dpm_manage_mutation_headers(
    headers: dict[str, str],
) -> dict[str, str]:
    """Replace caller-supplied workload authority with the Gateway-owned write contract."""

    resolved_authority = _authority_var.get()
    if resolved_authority is None:
        raise DpmManageRequestAuthorityError(
            "DPM Manage mutation authority is unavailable for this request."
        )
    return _replace_authority_headers(headers, resolved_authority.mutation_headers())


@contextmanager
def dpm_manage_request_authority_scope(
    authority: DpmManageRequestAuthority,
) -> Iterator[None]:
    """Provide an explicit scope for client-level contract tests and non-HTTP callers."""

    token: Token[DpmManageRequestAuthority | None] = _authority_var.set(authority)
    try:
        yield
    finally:
        _authority_var.reset(token)


def _replace_authority_headers(
    headers: dict[str, str],
    trusted_headers: dict[str, str],
) -> dict[str, str]:
    authorized = {
        name: value
        for name, value in headers.items()
        if name.lower() not in _AUTHORITY_HEADER_NAMES
    }
    authorized.update(trusted_headers)
    return authorized


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
