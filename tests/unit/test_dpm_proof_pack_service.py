import pytest
from fastapi import HTTPException

from app.services.dpm_proof_pack_service import DpmProofPackService


class _FakeDpmClient:
    def __init__(self, result: tuple):
        self.result = result
        self.calls: list[dict[str, object]] = []

    async def generate_proof_pack(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "proof_pack_generate",
                "body": body,
                "idempotency_key": idempotency_key,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_proof_pack(self, proof_pack_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "proof_pack_get",
                "proof_pack_id": proof_pack_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_proof_pack_markdown(self, proof_pack_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "proof_pack_markdown",
                "proof_pack_id": proof_pack_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_proof_pack_report_input(self, proof_pack_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "proof_pack_report_input",
                "proof_pack_id": proof_pack_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_proof_pack_ai_evidence_input(self, proof_pack_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "proof_pack_ai_evidence_input",
                "proof_pack_id": proof_pack_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result


@pytest.mark.asyncio
async def test_dpm_proof_pack_generation_preserves_manage_payload() -> None:
    manage_payload = _proof_pack_generate_payload()
    client = _FakeDpmClient((200, manage_payload))
    service = DpmProofPackService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.generate_proof_pack(
        body={"source_type": "REBALANCE_RUN", "rebalance_run_id": "rr_001"},
        idempotency_key="idem-proof-pack-1",
        correlation_id="corr-proof-pack-1",
    )

    assert response.correlation_id == "corr-proof-pack-1"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.supportability.authority == "lotus-manage:RFC-0040"
    assert response.supportability.state == "READY"
    assert response.supportability.proof_pack_id == "dpp_rr_001"
    assert response.supportability.content_hash == "sha256:proof-pack"
    assert response.supportability.reason_codes == [
        "AI_EVIDENCE_INPUT_READY",
        "MANDATE_SECTION_READY",
        "PROOF_PACK_READY",
        "REPORT_INPUT_READY",
        "RUN_SECTION_READY",
    ]
    assert response.supportability.section_state_counts == {"READY": 2, "DEGRADED": 1}
    assert response.supportability.markdown_available is True
    assert response.supportability.report_input_available is True
    assert response.supportability.ai_evidence_input_available is True
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "proof_pack_generate",
            "body": {"source_type": "REBALANCE_RUN", "rebalance_run_id": "rr_001"},
            "idempotency_key": "idem-proof-pack-1",
            "correlation_id": "corr-proof-pack-1",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_proof_pack_lookup_does_not_reconstruct_sections_or_hashes() -> None:
    manage_payload = _proof_pack_lookup_payload()
    client = _FakeDpmClient((200, manage_payload))
    service = DpmProofPackService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_proof_pack(
        proof_pack_id="dpp_rr_001",
        correlation_id="corr-proof-pack-get-1",
    )

    assert response.data == manage_payload
    assert response.supportability.state == "DEGRADED"
    assert response.supportability.section_state_counts == {"READY": 1, "DEGRADED": 1}
    assert response.data["proof_pack"]["source_hashes"] == {
        "mandate": "sha256:mandate",
        "rebalance_run": "sha256:run",
    }
    assert client.calls == [
        {
            "method": "proof_pack_get",
            "proof_pack_id": "dpp_rr_001",
            "correlation_id": "corr-proof-pack-get-1",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_proof_pack_markdown_preserves_manage_text() -> None:
    client = _FakeDpmClient((200, "# DPM proof pack\n\n- Status: READY\n", {}))
    service = DpmProofPackService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_proof_pack_markdown(
        proof_pack_id="dpp_rr_001",
        correlation_id="corr-proof-pack-md-1",
    )

    assert response.source_service == "lotus-manage"
    assert response.proof_pack_id == "dpp_rr_001"
    assert response.markdown == "# DPM proof pack\n\n- Status: READY\n"
    assert client.calls == [
        {
            "method": "proof_pack_markdown",
            "proof_pack_id": "dpp_rr_001",
            "correlation_id": "corr-proof-pack-md-1",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_proof_pack_handoff_inputs_preserve_manage_payloads() -> None:
    report_payload = {
        "proof_pack_id": "dpp_rr_001",
        "report_input_ref": "report-input:dpp_rr_001",
        "section_hashes": {"mandate": "sha256:mandate"},
    }
    ai_payload = {
        "proof_pack_id": "dpp_rr_001",
        "ai_evidence_input_ref": "ai-evidence:dpp_rr_001",
        "reason_codes": ["AI_EVIDENCE_INPUT_READY"],
    }

    report_response = await DpmProofPackService(  # type: ignore[arg-type]
        dpm_client=_FakeDpmClient((200, report_payload))
    ).get_proof_pack_report_input(
        proof_pack_id="dpp_rr_001",
        correlation_id="corr-report-input-1",
    )
    ai_response = await DpmProofPackService(  # type: ignore[arg-type]
        dpm_client=_FakeDpmClient((200, ai_payload))
    ).get_proof_pack_ai_evidence_input(
        proof_pack_id="dpp_rr_001",
        correlation_id="corr-ai-input-1",
    )

    assert report_response.data == report_payload
    assert report_response.supportability.report_input_available is True
    assert ai_response.data == ai_payload
    assert ai_response.supportability.reason_codes == ["AI_EVIDENCE_INPUT_READY"]
    assert ai_response.supportability.ai_evidence_input_available is True


@pytest.mark.asyncio
async def test_dpm_proof_pack_forwards_manage_errors_as_product_safe_detail() -> None:
    client = _FakeDpmClient((503, {"detail": "upstream communication failure: TimeoutException"}))
    service = DpmProofPackService(dpm_client=client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        await service.get_proof_pack(
            proof_pack_id="dpp_missing",
            correlation_id="corr-proof-pack-error-1",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == {
        "source_service": "lotus-manage",
        "upstream_status": 503,
        "error_code": "MANAGE_PROOF_PACK_UPSTREAM_ERROR",
        "detail": "upstream communication failure: TimeoutException",
    }


def _proof_pack_generate_payload() -> dict[str, object]:
    return {
        "proof_pack": {
            "proof_pack_id": "dpp_rr_001",
            "status": "READY",
            "content_hash": "sha256:proof-pack",
            "reason_codes": ["PROOF_PACK_READY"],
            "sections": [
                {
                    "section_id": "mandate",
                    "state": "READY",
                    "reason_codes": ["MANDATE_SECTION_READY"],
                },
                {"section_id": "run", "state": "READY", "reason_codes": ["RUN_SECTION_READY"]},
                {"section_id": "tax", "state": "DEGRADED"},
            ],
            "report_input_ref": "report-input:dpp_rr_001",
            "ai_evidence_input_ref": "ai-evidence:dpp_rr_001",
        },
        "markdown_url": "/api/v1/rebalance/proof-packs/dpp_rr_001/summary.md",
        "report_input_url": "/api/v1/rebalance/proof-packs/dpp_rr_001/report-input",
        "ai_evidence_input_url": "/api/v1/rebalance/proof-packs/dpp_rr_001/ai-evidence-input",
        "reason_codes": ["REPORT_INPUT_READY", "AI_EVIDENCE_INPUT_READY"],
    }


def _proof_pack_lookup_payload() -> dict[str, object]:
    return {
        "proof_pack": {
            "proof_pack_id": "dpp_rr_001",
            "status": "DEGRADED",
            "content_hash": "sha256:proof-pack",
            "source_hashes": {
                "mandate": "sha256:mandate",
                "rebalance_run": "sha256:run",
            },
            "sections": [
                {"section_id": "mandate", "state": "READY"},
                {
                    "section_id": "tax",
                    "state": "DEGRADED",
                    "reason_codes": ["TAX_LOT_SOURCE_MISSING"],
                },
            ],
        }
    }
