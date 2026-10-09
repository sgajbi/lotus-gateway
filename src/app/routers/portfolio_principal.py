"""Finite verified-principal pilot for the exact-portfolio tax-lot read."""

import os
from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.middleware.caller_identity import admit_caller_tenant, release_caller_identity
from app.services.principal_authority.contracts import (
    PrincipalDenied,
    PrincipalGrantResolver,
    ResolvedPrincipal,
)

_bearer = HTTPBearer(auto_error=False, scheme_name="PortfolioPrincipalCredential")


async def portfolio_principal_dependency(
    request: Request,
    portfolio_id: str,
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AsyncIterator[ResolvedPrincipal | None]:
    posture = os.getenv("PORTFOLIO_TAX_LOT_PRINCIPAL_POSTURE", "header-trust")
    if posture == "header-trust" and os.getenv("ENVIRONMENT", "local") in {"local", "dev"}:
        yield None
        return
    if posture != "verified":
        raise HTTPException(503, detail={"code": "grant_store_unavailable"})
    if len(request.headers.getlist("Authorization")) > 1:
        raise HTTPException(401, detail={"code": "malformed_credential"})
    if authorization is None:
        code = (
            "malformed_credential" if "Authorization" in request.headers else "missing_credential"
        )
        raise HTTPException(401, detail={"code": code})
    resolver = cast(
        PrincipalGrantResolver | None, getattr(request.app.state, "principal_grant_resolver", None)
    )
    if resolver is None:
        raise HTTPException(503, detail={"code": "grant_store_unavailable"})
    try:
        principal = await resolver.resolve(
            authorization.credentials,
            required_capabilities=frozenset({"portfolio.read"}),
            requested_portfolios=frozenset({portfolio_id}),
        )
    except PrincipalDenied as denial:
        raise HTTPException(denial.status_code, detail={"code": denial.denial_class}) from None
    token = admit_caller_tenant(principal.tenant_id)
    try:
        yield principal
    finally:
        release_caller_identity(token)


PortfolioPrincipal = Annotated[ResolvedPrincipal | None, Depends(portfolio_principal_dependency)]
