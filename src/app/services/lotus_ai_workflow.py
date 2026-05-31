"""Shared guards for governed lotus-ai workflow-pack handoffs."""

from fastapi import HTTPException, status

from app.clients.lotus_ai_client import LotusAiClient

LOTUS_AI_NOT_CONFIGURED_DETAIL = "lotus-ai workflow-pack execution is not configured for Gateway."


def require_lotus_ai_client(client: LotusAiClient | None) -> LotusAiClient:
    """Return a configured lotus-ai client or raise the standard Gateway service error."""

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=LOTUS_AI_NOT_CONFIGURED_DETAIL,
        )
    return client
