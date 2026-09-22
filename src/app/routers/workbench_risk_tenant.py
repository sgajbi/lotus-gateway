"""One explicit tenant-admission boundary for stateful Workbench Risk routes."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request


def admit_workbench_risk_tenant(
    request: Request,
    tenant_id: Annotated[
        str,
        Header(
            alias="X-Tenant-Id",
            pattern=r"\S",
            min_length=1,
            max_length=128,
            description=(
                "Caller-presented tenant scope required by lotus-risk for stateful analytics. "
                "One nonblank identifier of at most 128 characters; Gateway forwards its "
                "admitted scope without substituting a tenant or grant."
            ),
            examples=["tenant-sg"],
        ),
    ],
) -> str:
    values = request.headers.getlist("X-Tenant-Id")
    normalized = tenant_id.strip()
    if len(values) != 1 or not normalized:
        raise HTTPException(status_code=400, detail="Invalid X-Tenant-Id for stateful Risk.")
    if len(normalized) > 128:
        raise HTTPException(status_code=400, detail="X-Tenant-Id exceeds 128 characters.")
    return normalized


RiskTenantId = Annotated[str, Depends(admit_workbench_risk_tenant)]
