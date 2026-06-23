from dataclasses import dataclass
from typing import Any

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
        return headers


def idea_error_response(status_code: int, *, description: str) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": IdeaGatewayErrorResponse,
            "description": description,
        }
    }
