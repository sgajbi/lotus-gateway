from typing import cast

import pytest
from fastapi import HTTPException, status

from app.clients.lotus_ai_client import LotusAiClient
from app.services.lotus_ai_workflow import (
    LOTUS_AI_NOT_CONFIGURED_DETAIL,
    require_lotus_ai_client,
)


def test_require_lotus_ai_client_returns_configured_client() -> None:
    client = cast(LotusAiClient, object())

    assert require_lotus_ai_client(client) is client


def test_require_lotus_ai_client_raises_product_safe_unavailable_error() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_lotus_ai_client(None)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc_info.value.detail == LOTUS_AI_NOT_CONFIGURED_DETAIL
