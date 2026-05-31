import pytest
from fastapi import HTTPException

from app.contracts.bank_demo_proof import BankDemoProofEnvelopeResponse
from app.contracts.dpm_construction import (
    DpmConstructionErrorDetail,
    DpmConstructionGatewayResponse,
    DpmConstructionSupportability,
)
from app.services.upstream_envelope import (
    build_gateway_envelope,
    build_upstream_status_gateway_envelope,
    raise_for_upstream_error,
    raise_product_safe_upstream_error,
    safe_upstream_detail,
)


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


def test_build_upstream_status_gateway_envelope_preserves_supportability() -> None:
    payload = {"alternative_set_id": "cas_1", "status": "READY"}
    supportability = DpmConstructionSupportability(state="READY", reason_codes=["READY"])

    response = build_upstream_status_gateway_envelope(
        DpmConstructionGatewayResponse,
        correlation_id="corr-construction",
        upstream_status=200,
        upstream_payload=payload,
        supportability=supportability,
    )

    assert response.correlation_id == "corr-construction"
    assert response.upstream_status == 200
    assert response.supportability == supportability
    assert response.data == payload


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


def test_safe_upstream_detail_uses_bounded_message_fields() -> None:
    assert safe_upstream_detail(
        {"detail": {"reason": "blocked"}},
        default_detail="fallback",
    ) == str({"reason": "blocked"})
    assert safe_upstream_detail({}, default_detail="fallback") == "fallback"


def test_raise_product_safe_upstream_error_builds_typed_detail() -> None:
    with pytest.raises(HTTPException) as exc_info:
        raise_product_safe_upstream_error(
            409,
            {"message": "CONSTRUCTION_IDEMPOTENCY_KEY_CONFLICT"},
            error_model=DpmConstructionErrorDetail,
            error_code="MANAGE_CONSTRUCTION_UPSTREAM_ERROR",
            default_detail="lotus-manage construction request failed",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "source_service": "lotus-manage",
        "upstream_status": 409,
        "error_code": "MANAGE_CONSTRUCTION_UPSTREAM_ERROR",
        "detail": "CONSTRUCTION_IDEMPOTENCY_KEY_CONFLICT",
    }
