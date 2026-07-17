from dataclasses import dataclass
from typing import Any

from fastapi import Header

from app.contracts.ideas import IdeaGatewayErrorResponse


@dataclass(frozen=True)
class IdeaCallerHeaders:
    subject: str | None
    roles: str | None
    capabilities: str | None
    tenant_ids: str | None = None
    book_ids: str | None = None
    portfolio_ids: str | None = None
    client_ids: str | None = None
    trusted_caller_context: str | None = None

    def as_idea_context(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.subject:
            headers["X-Caller-Subject"] = self.subject
        if self.roles:
            headers["X-Caller-Roles"] = self.roles
        if self.capabilities:
            headers["X-Caller-Capabilities"] = self.capabilities
        if self.tenant_ids:
            headers["X-Caller-Tenant-Ids"] = self.tenant_ids
        if self.book_ids:
            headers["X-Caller-Book-Ids"] = self.book_ids
        if self.portfolio_ids:
            headers["X-Caller-Portfolio-Ids"] = self.portfolio_ids
        if self.client_ids:
            headers["X-Caller-Client-Ids"] = self.client_ids
        if self.trusted_caller_context:
            headers["X-Lotus-Trusted-Caller-Context"] = self.trusted_caller_context
        return headers


def idea_caller_headers(
    x_caller_subject: str | None = Header(default=None, alias="X-Caller-Subject"),
    x_caller_roles: str | None = Header(default=None, alias="X-Caller-Roles"),
    x_caller_capabilities: str | None = Header(default=None, alias="X-Caller-Capabilities"),
    x_caller_tenant_ids: str | None = Header(default=None, alias="X-Caller-Tenant-Ids"),
    x_caller_book_ids: str | None = Header(default=None, alias="X-Caller-Book-Ids"),
    x_caller_portfolio_ids: str | None = Header(default=None, alias="X-Caller-Portfolio-Ids"),
    x_caller_client_ids: str | None = Header(default=None, alias="X-Caller-Client-Ids"),
    x_lotus_trusted_caller_context: str | None = Header(
        default=None,
        alias="X-Lotus-Trusted-Caller-Context",
    ),
) -> IdeaCallerHeaders:
    """Maps trusted transport context without deriving any Idea authority locally."""
    return IdeaCallerHeaders(
        subject=x_caller_subject,
        roles=x_caller_roles,
        capabilities=x_caller_capabilities,
        tenant_ids=x_caller_tenant_ids,
        book_ids=x_caller_book_ids,
        portfolio_ids=x_caller_portfolio_ids,
        client_ids=x_caller_client_ids,
        trusted_caller_context=x_lotus_trusted_caller_context,
    )


def idea_error_response(status_code: int, *, description: str) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": IdeaGatewayErrorResponse,
            "description": description,
        }
    }
