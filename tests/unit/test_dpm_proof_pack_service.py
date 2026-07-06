from typing import Any, cast

import pytest
from fastapi import HTTPException

from app.contracts.dpm_proof_packs import DpmProofPackMemoRequest
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


class _FakeLotusAiClient:
    def __init__(self, result: tuple):
        self.result = result
        self.calls: list[dict[str, object]] = []

    async def execute_workflow_pack(self, **kwargs):  # noqa: ANN003
        self.calls.append(kwargs)
        return self.result


@pytest.mark.asyncio
async def test_dpm_proof_pack_generation_preserves_manage_payload() -> None:
    manage_payload = _proof_pack_generate_payload()
    client = _FakeDpmClient((200, manage_payload))
    service = DpmProofPackService(dpm_client=client)

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
    service = DpmProofPackService(dpm_client=client)

    response = await service.get_proof_pack(
        proof_pack_id="dpp_rr_001",
        correlation_id="corr-proof-pack-get-1",
    )

    assert response.data == manage_payload
    assert response.supportability.state == "DEGRADED"
    assert response.supportability.section_state_counts == {"READY": 1, "DEGRADED": 1}
    proof_pack = cast(dict[str, Any], response.data["proof_pack"])
    assert proof_pack["source_hashes"] == {
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
    service = DpmProofPackService(dpm_client=client)

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

    report_response = await DpmProofPackService(
        dpm_client=_FakeDpmClient((200, report_payload))
    ).get_proof_pack_report_input(
        proof_pack_id="dpp_rr_001",
        correlation_id="corr-report-input-1",
    )
    ai_response = await DpmProofPackService(
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
async def test_dpm_proof_pack_pm_memo_executes_lotus_ai_with_manage_evidence() -> None:
    manage_payload = {
        "contract_version": "DpmProofPackAiEvidenceInput.v1",
        "proof_pack_id": "dpp_rr_001",
        "proof_pack_content_hash": "sha256:proof-pack",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "as_of_date": "2026-05-03",
        "permitted_use": ["pm_memo_support"],
        "forbidden_actions": [
            "place_orders",
            "approve_rebalance",
            "override_controls",
            "invent_missing_evidence",
            "contact_client",
        ],
        "forbidden_fields_removed": ["client_name"],
        "decision_summary": {"decision": "rebalance_ready"},
        "supportability_status": "SUPPORTED",
        "reason_codes": ["AI_EVIDENCE_INPUT_READY"],
        "sections": [{"section_id": "mandate", "state": "READY"}],
        "source_refs": ["lotus-manage:proof-pack:dpp_rr_001"],
        "evidence_ref": "ai-evidence:dpp_rr_001",
        "content_hash": "sha256:ai-evidence",
    }
    ai_payload = {
        "execution": {
            "audit": {"workflow_pack_run_id": "packrun_dpp_rr_001"},
            "result": {"dpm_pm_memo_status": "REVIEW_REQUIRED"},
        },
        "workflow_pack_run": {
            "run_id": "packrun_dpp_rr_001",
            "workflow_authority_owner": "lotus-manage",
            "review_state": "AWAITING_REVIEW",
        },
    }
    dpm_client = _FakeDpmClient((200, manage_payload))
    ai_client = _FakeLotusAiClient((200, ai_payload))
    service = DpmProofPackService(
        dpm_client=dpm_client,
        lotus_ai_client=ai_client,
    )

    response = await service.request_proof_pack_pm_memo(
        proof_pack_id="dpp_rr_001",
        request=DpmProofPackMemoRequest(
            requested_outputs=["pm_memo", "evidence_gaps"],
            audience=["portfolio_manager"],
        ),
        correlation_id="corr-proof-pack-memo-1",
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.manage_upstream_status == 200
    assert response.ai_upstream_status == 200
    assert response.supportability.state == "SUPPORTED"
    assert response.ai_evidence_input == manage_payload
    assert response.memo_request == {
        "requested_outputs": ["pm_memo", "evidence_gaps"],
        "audience": ["portfolio_manager"],
    }
    workflow_pack_run = cast(dict[str, Any], response.data["workflow_pack_run"])
    assert workflow_pack_run["workflow_authority_owner"] == "lotus-manage"
    [ai_call] = ai_client.calls
    assert ai_call["pack_id"] == "dpm_pm_memo.pack"
    assert ai_call["version"] == "v1"
    assert ai_call["workflow_surface"] == "dpm-proof-pack-ai-evidence"
    assert ai_call["correlation_id"] == "corr-proof-pack-memo-1"
    task_request = cast(dict[str, Any], ai_call["task_request"])
    task_context = cast(dict[str, Any], task_request["context"])
    task_payload = cast(dict[str, Any], task_context["payload"])
    assert task_request["task_id"] == "explain.v1"
    assert task_payload["ai_evidence_input"] == manage_payload
    assert task_payload["memo_request"] == response.memo_request
    supportability = cast(dict[str, Any], task_payload["supportability"])
    assert supportability["blocked_actions"] == [
        "place_orders",
        "approve_rebalance",
        "override_controls",
        "invent_missing_evidence",
        "contact_client",
    ]
    assert task_context["source_refs"] == [
        "lotus-manage:proof-pack-ai-evidence:ai-evidence:dpp_rr_001",
        "lotus-manage:proof-pack-ai-evidence:dpp_rr_001",
        "lotus-manage:proof-pack:dpp_rr_001",
    ]


@pytest.mark.asyncio
async def test_dpm_proof_pack_pm_memo_requires_lotus_ai_client() -> None:
    service = DpmProofPackService(dpm_client=_FakeDpmClient((200, {})))

    with pytest.raises(HTTPException) as exc_info:
        await service.request_proof_pack_pm_memo(
            proof_pack_id="dpp_rr_001",
            request=DpmProofPackMemoRequest(),
            correlation_id="corr-proof-pack-memo-missing-ai",
        )

    assert exc_info.value.status_code == 503
    assert (
        exc_info.value.detail == "lotus-ai workflow-pack execution is not configured for Gateway."
    )


@pytest.mark.asyncio
async def test_dpm_proof_pack_pm_memo_preserves_lotus_ai_error() -> None:
    service = DpmProofPackService(
        dpm_client=_FakeDpmClient((200, {"proof_pack_id": "dpp_rr_001"})),
        lotus_ai_client=_FakeLotusAiClient(
            (422, {"detail": "PROOF_PACK_PM_MEMO_GUARDRAIL_BLOCKED: missing content_hash"})
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.request_proof_pack_pm_memo(
            proof_pack_id="dpp_rr_001",
            request=DpmProofPackMemoRequest(),
            correlation_id="corr-proof-pack-memo-ai-error",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == {
        "source_service": "lotus-ai",
        "upstream_status": 422,
        "error_code": "AI_PROOF_PACK_PM_MEMO_UPSTREAM_ERROR",
        "detail": "lotus-ai proof-pack PM memo request failed",
    }


@pytest.mark.asyncio
async def test_dpm_proof_pack_forwards_manage_errors_as_product_safe_detail() -> None:
    client = _FakeDpmClient((503, {"detail": "upstream communication failure: TimeoutException"}))
    service = DpmProofPackService(dpm_client=client)

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
        "detail": "lotus-manage proof-pack request failed",
    }


def _proof_pack_generate_payload() -> dict[str, Any]:
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


def _proof_pack_lookup_payload() -> dict[str, Any]:
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
