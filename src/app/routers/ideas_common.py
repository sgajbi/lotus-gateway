from dataclasses import dataclass
from typing import Any

from app.contracts.ideas import IdeaGatewayErrorResponse


@dataclass(frozen=True)
class IdeaCallerHeaders:
    subject: str | None
    roles: str | None
    capabilities: str | None

    def as_idea_context(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.subject:
            headers["X-Caller-Subject"] = self.subject
        if self.roles:
            headers["X-Caller-Roles"] = self.roles
        if self.capabilities:
            headers["X-Caller-Capabilities"] = self.capabilities
        return headers


def idea_error_response(status_code: int, *, description: str) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": IdeaGatewayErrorResponse,
            "description": description,
        }
    }
