from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header

from app.services.caller_context import caller_context_headers


def reporting_context_headers(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
    capabilities: str | None = None,
    portfolio_ids: str | None = None,
    client_ids: str | None = None,
    book_ids: str | None = None,
) -> dict[str, str]:
    headers = caller_context_headers(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
    entitlement_headers = {
        "X-Caller-Capabilities": capabilities,
        "X-Caller-Portfolio-Ids": portfolio_ids,
        "X-Caller-Client-Ids": client_ids,
        "X-Caller-Book-Ids": book_ids,
    }
    headers.update(
        {
            name: value.strip()
            for name, value in entitlement_headers.items()
            if value and value.strip()
        }
    )
    return headers


@dataclass(frozen=True)
class ReportingCallerHeaderInputs:
    actor_id: str | None
    caller_application: str | None
    tenant_id: str | None
    region: str | None
    booking_center_code: str | None
    role: str | None
    capabilities: str | None = None
    portfolio_ids: str | None = None
    client_ids: str | None = None
    book_ids: str | None = None

    def as_headers(self) -> dict[str, str]:
        return reporting_context_headers(
            actor_id=self.actor_id,
            caller_application=self.caller_application,
            tenant_id=self.tenant_id,
            region=self.region,
            booking_center_code=self.booking_center_code,
            role=self.role,
            capabilities=self.capabilities,
            portfolio_ids=self.portfolio_ids,
            client_ids=self.client_ids,
            book_ids=self.book_ids,
        )


def reporting_context_dependency(
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> dict[str, str]:
    return reporting_context_headers(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )


ReportingCallerContext = Annotated[dict[str, str], Depends(reporting_context_dependency)]
