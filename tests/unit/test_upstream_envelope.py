import pytest
from fastapi import HTTPException

from app.contracts.bank_demo_proof import BankDemoProofEnvelopeResponse
from app.services.upstream_envelope import build_gateway_envelope, raise_for_upstream_error


def test_build_gateway_envelope_preserves_payload_and_aliases() -> None:
    payload = {
        "proof_marker": "BANK_DEMO_PROOF_PACK_CREATED",
        "client_ready_posture": "CLIENT_READY_PUBLICATION_BLOCKED",
    }

    response = build_gateway_envelope(
        BankDemoProofEnvelopeResponse,
        correlation_id="corr-proof",
        upstream_payload=payload,
    )

    assert response.correlation_id == "corr-proof"
    assert response.data == payload
    assert response.model_dump(by_alias=True)["correlationId"] == "corr-proof"


def test_raise_for_upstream_error_preserves_payload_by_default() -> None:
    payload = {"detail": {"reason": "material_review_blocked"}}

    with pytest.raises(HTTPException) as exc_info:
        raise_for_upstream_error(409, payload)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == payload


def test_raise_for_upstream_error_can_preserve_legacy_stringified_payload() -> None:
    payload = {"detail": {"reason": "client_ready_blocked"}}

    with pytest.raises(HTTPException) as exc_info:
        raise_for_upstream_error(409, payload, stringify_payload=True)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == str(payload)
