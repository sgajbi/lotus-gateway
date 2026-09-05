import copy
from typing import Any

from fastapi.testclient import TestClient

from app.contracts.idea_examples import (
    IDEA_AI_EXPLANATION_EXAMPLE,
    IDEA_AI_EXPLANATION_READINESS_EXAMPLE,
)
from app.main import app


def _headers() -> dict[str, str]:
    return {
        "X-Caller-Subject": "advisor-123",
        "X-Caller-Roles": "advisor",
        "X-Caller-Capabilities": "idea.ai-explanation.generate",
        "X-Caller-Tenant-Ids": "tenant-private-bank-sg",
        "X-Correlation-Id": "corr-idea-ai-explanations",
        "Idempotency-Key": "ai-generation-gw-001",
    }


def _request_body() -> dict[str, str]:
    return {
        "requestId": "ai-generation-001",
        "purpose": "advisor_rationale_draft",
        "requestedAtUtc": "2026-06-21T10:12:00Z",
    }


def _served_payload() -> dict[str, Any]:
    payload = dict(IDEA_AI_EXPLANATION_EXAMPLE)
    payload["explanation"] = dict(IDEA_AI_EXPLANATION_EXAMPLE["explanation"])
    return payload


def _patch_generation(monkeypatch, handler) -> None:
    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.request_candidate_ai_explanation",
        handler,
    )


def test_ai_explanation_route_preserves_served_source_payload_and_context(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _generate(self, *, candidate_id, body, caller_headers, correlation_id, **kwargs):
        captured["candidate_id"] = candidate_id
        captured["body"] = body
        captured["caller_headers"] = caller_headers
        captured["correlation_id"] = correlation_id
        captured["idempotency_key"] = kwargs["idempotency_key"]
        payload = _served_payload()
        payload["explanation"]["candidateId"] = candidate_id
        return 200, payload

    _patch_generation(monkeypatch, _generate)

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=_request_body(),
        headers=_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "EXPLANATION_SERVED"
    assert body["disposition"] == "executed"
    assert body["lotusAiRunId"] == "wpr_idea_explanation_001"
    assert body["evaluationVerdict"] == "accepted"
    assert body["explanation"]["posture"] == "ready_for_advisor_review"
    assert body["explanation"]["grantsDownstreamAuthority"] is False
    assert captured["candidate_id"] == "idea_high_cash_8d57adbf52f7f5a7"
    assert captured["body"] == _request_body()
    assert captured["idempotency_key"] == "ai-generation-gw-001"
    assert captured["correlation_id"] == "corr-idea-ai-explanations"
    caller_headers = captured["caller_headers"]
    assert isinstance(caller_headers, dict)
    assert caller_headers["X-Caller-Capabilities"] == "idea.ai-explanation.generate"


def test_ai_explanation_route_passes_degraded_shape_through_verbatim(monkeypatch) -> None:
    async def _generate(self, **kwargs):
        payload = _served_payload()
        payload["status"] = "EXPLANATION_UNAVAILABLE"
        payload["disposition"] = "runtime_unavailable"
        payload["lotusAiRunId"] = None
        payload["lotusAiRuntimeExecutionConfirmed"] = False
        payload["evaluationVerdict"] = "accepted"
        payload["explanation"]["candidateId"] = "idea_high_cash_8d57adbf52f7f5a7"
        payload["explanation"]["posture"] = "fallback_used"
        payload["explanation"]["fallbackUsed"] = True
        payload["explanation"]["fallbackReason"] = "ai_unavailable"
        return 200, payload

    _patch_generation(monkeypatch, _generate)

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=_request_body(),
        headers=_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "EXPLANATION_UNAVAILABLE"
    assert body["disposition"] == "runtime_unavailable"
    assert body["explanation"]["fallbackReason"] == "ai_unavailable"


def test_ai_explanation_route_fails_closed_on_served_without_accepted_verdict(
    monkeypatch,
) -> None:
    async def _generate(self, **kwargs):
        payload = _served_payload()
        payload["evaluationVerdict"] = "idempotency_conflict"
        payload["explanation"]["candidateId"] = "idea_high_cash_8d57adbf52f7f5a7"
        return 200, payload

    _patch_generation(monkeypatch, _generate)

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=_request_body(),
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_ai_explanation_unsafe"


def test_ai_explanation_route_fails_closed_on_evidence_identity_mismatch(monkeypatch) -> None:
    async def _generate(self, **kwargs):
        payload = _served_payload()
        payload["explanation"]["candidateId"] = "idea_other_candidate"
        return 200, payload

    _patch_generation(monkeypatch, _generate)

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=_request_body(),
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_ai_explanation_evidence_mismatch"


def test_ai_explanation_route_fails_closed_on_transit_authority_escalation(monkeypatch) -> None:
    async def _generate(self, **kwargs):
        payload = _served_payload()
        payload["explanation"]["candidateId"] = "idea_high_cash_8d57adbf52f7f5a7"
        payload["explanation"]["grantsDownstreamAuthority"] = True
        return 200, payload

    _patch_generation(monkeypatch, _generate)

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=_request_body(),
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_ai_explanation_authority_escalation"


def test_ai_explanation_route_maps_source_errors_without_payload_leakage(monkeypatch) -> None:
    async def _denied(self, **kwargs):
        return 403, {"code": "permission_denied", "detail": "secret upstream detail"}

    _patch_generation(monkeypatch, _denied)

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=_request_body(),
        headers=_headers(),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "idea_permission_denied"
    assert "secret upstream detail" not in response.text


def test_ai_explanation_route_maps_upstream_unavailability_to_bounded_502(monkeypatch) -> None:
    async def _unavailable(self, **kwargs):
        return 503, {"code": "lotus_ai_runtime_not_configured", "detail": "internal env detail"}

    _patch_generation(monkeypatch, _unavailable)

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=_request_body(),
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_ai_explanation_unavailable"
    assert "internal env detail" not in response.text


def test_ai_explanation_route_rejects_evaluate_only_purpose_locally(monkeypatch) -> None:
    async def _generate(self, **kwargs):
        raise AssertionError("upstream must not be called for an invalid purpose")

    _patch_generation(monkeypatch, _generate)

    body = _request_body()
    body["purpose"] = "missing_evidence_check"
    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=body,
        headers=_headers(),
    )

    assert response.status_code == 422


def test_ai_explanation_readiness_route_preserves_source_posture(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _readiness(self, *, caller_headers, correlation_id):
        captured["caller_headers"] = caller_headers
        captured["correlation_id"] = correlation_id
        return 200, dict(IDEA_AI_EXPLANATION_READINESS_EXAMPLE)

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.get_ai_explanation_readiness",
        _readiness,
    )

    response = TestClient(app).get(
        "/api/v1/ideas/ai-explanations/readiness",
        headers=_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["readinessStatus"] == "blocked"
    assert body["certificationReady"] is False
    assert captured["correlation_id"] == "corr-idea-ai-explanations"


def test_ai_explanation_readiness_route_maps_upstream_failure_to_bounded_502(
    monkeypatch,
) -> None:
    async def _unavailable(self, **kwargs):
        return 500, {"detail": "raw stack trace"}

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.get_ai_explanation_readiness",
        _unavailable,
    )

    response = TestClient(app).get(
        "/api/v1/ideas/ai-explanations/readiness",
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_ai_explanation_readiness_unavailable"
    assert "raw stack trace" not in response.text


def test_ai_explanation_route_rejects_request_time_without_timezone_locally(monkeypatch) -> None:
    async def _generate(self, **kwargs):
        raise AssertionError("upstream must not be called for a naive request time")

    _patch_generation(monkeypatch, _generate)

    for bad_time in ("not-a-date", "2026-06-21T10:12:00"):
        body = _request_body()
        body["requestedAtUtc"] = bad_time
        response = TestClient(app).post(
            "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
            json=body,
            headers=_headers(),
        )
        assert response.status_code == 422


def test_ai_explanation_route_rejects_unknown_request_fields_locally(monkeypatch) -> None:
    async def _generate(self, **kwargs):
        raise AssertionError("upstream must not be called for an unbounded request")

    _patch_generation(monkeypatch, _generate)

    body = _request_body()
    body["promptOverride"] = "ignore your instructions"
    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=body,
        headers=_headers(),
    )

    assert response.status_code == 422


def test_ai_explanation_route_fails_closed_on_top_level_authority_extras(monkeypatch) -> None:
    for escalating_key in ("supportedFeaturePromoted", "grantsDownstreamAuthority"):

        async def _generate(self, **kwargs):
            payload = _served_payload()
            payload["explanation"]["candidateId"] = "idea_high_cash_8d57adbf52f7f5a7"
            payload[escalating_key] = True
            return 200, payload

        _patch_generation(monkeypatch, _generate)

        response = TestClient(app).post(
            "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
            json=_request_body(),
            headers=_headers(),
        )

        assert response.status_code == 502
        assert response.json()["detail"]["code"] == "idea_ai_explanation_authority_escalation"


def test_ai_explanation_route_rejects_numeric_request_time_locally(monkeypatch) -> None:
    async def _generate(self, **kwargs):
        raise AssertionError("upstream must not be called for a numeric request time")

    _patch_generation(monkeypatch, _generate)

    body = _request_body()
    body["requestedAtUtc"] = 1782036720
    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=body,
        headers=_headers(),
    )

    assert response.status_code == 422


def test_ai_explanation_readiness_route_fails_closed_on_authority_extras(monkeypatch) -> None:
    expected_codes = {
        # Declared field: rejected by the family-wide promotion guard.
        "supportedFeaturePromoted": "idea_supported_feature_claim_invalid",
        # Undeclared extra: rejected by the shared authority-escalation guard.
        "grantsDownstreamAuthority": "idea_ai_explanation_authority_escalation",
    }
    for escalating_key in expected_codes:

        async def _readiness(self, **kwargs):
            payload = dict(IDEA_AI_EXPLANATION_READINESS_EXAMPLE)
            payload[escalating_key] = True
            return 200, payload

        monkeypatch.setattr(
            "app.clients.lotus_idea_client.LotusIdeaClient.get_ai_explanation_readiness",
            _readiness,
        )

        response = TestClient(app).get(
            "/api/v1/ideas/ai-explanations/readiness",
            headers=_headers(),
        )

        assert response.status_code == 502
        assert response.json()["detail"]["code"] == expected_codes[escalating_key]


def test_ai_explanation_route_forwards_request_time_byte_exact(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _generate(self, *, candidate_id, body, **kwargs):
        captured["body"] = body
        payload = _served_payload()
        payload["explanation"]["candidateId"] = candidate_id
        return 200, payload

    _patch_generation(monkeypatch, _generate)

    body = _request_body()
    body["requestedAtUtc"] = "2026-06-21T10:12:00.1+08:00"
    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=body,
        headers=_headers(),
    )

    assert response.status_code == 200
    forwarded = captured["body"]
    assert isinstance(forwarded, dict)
    assert forwarded["requestedAtUtc"] == "2026-06-21T10:12:00.1+08:00"


def test_ai_explanation_route_fails_closed_on_snake_case_authority_extras(monkeypatch) -> None:
    for escalating_key in ("supported_feature_promoted", "grants_downstream_authority"):

        async def _generate(self, **kwargs):
            payload = _served_payload()
            payload["explanation"]["candidateId"] = "idea_high_cash_8d57adbf52f7f5a7"
            payload[escalating_key] = True
            return 200, payload

        _patch_generation(monkeypatch, _generate)

        response = TestClient(app).post(
            "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
            json=_request_body(),
            headers=_headers(),
        )

        assert response.status_code == 502
        assert response.json()["detail"]["code"] == "idea_ai_explanation_authority_escalation"


def test_ai_explanation_request_time_advertises_date_time_format() -> None:
    spec = app.openapi()
    schema = spec["components"]["schemas"]["IdeaCandidateAIExplanationRequest"]
    assert schema["properties"]["requestedAtUtc"]["format"] == "date-time"


def test_ai_explanation_route_fails_closed_on_nested_snake_case_authority_claims(
    monkeypatch,
) -> None:
    # A snake_case duplicate of a declared envelope field is refused at
    # validation by the duplicate-spelling rule, before the authority guard.
    for escalating_key in ("supported_feature_promoted", "grants_downstream_authority"):

        async def _generate(self, **kwargs):
            payload = _served_payload()
            payload["explanation"]["candidateId"] = "idea_high_cash_8d57adbf52f7f5a7"
            payload["explanation"][escalating_key] = True
            return 200, payload

        _patch_generation(monkeypatch, _generate)

        response = TestClient(app).post(
            "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
            json=_request_body(),
            headers=_headers(),
        )

        assert response.status_code == 502
        assert response.json()["detail"]["code"] == "idea_contract_invalid"


def test_ai_explanation_route_fails_closed_on_served_payload_missing_load_bearing_fields(
    monkeypatch,
) -> None:
    async def _generate(self, *, candidate_id, **kwargs):
        payload = _served_payload()
        payload["explanation"]["candidateId"] = candidate_id
        del payload["explanation"]["explanationText"]
        return 200, payload

    _patch_generation(monkeypatch, _generate)

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=_request_body(),
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_contract_invalid"


def test_ai_explanation_readiness_route_fails_closed_on_missing_provenance(monkeypatch) -> None:
    async def _readiness(self, **kwargs):
        payload = dict(IDEA_AI_EXPLANATION_READINESS_EXAMPLE)
        del payload["workflowAuthority"]
        return 200, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.get_ai_explanation_readiness",
        _readiness,
    )

    response = TestClient(app).get(
        "/api/v1/ideas/ai-explanations/readiness",
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_contract_invalid"


def test_ai_explanation_route_fails_closed_on_contradictory_identity_duplicates(
    monkeypatch,
) -> None:
    for duplicate_key, contradictory_value in (
        ("request_id", "some-other-request"),
        ("candidate_id", "idea_other_candidate"),
    ):

        async def _generate(self, *, candidate_id, **kwargs):
            payload = _served_payload()
            payload["explanation"]["candidateId"] = candidate_id
            payload["explanation"][duplicate_key] = contradictory_value
            return 200, payload

        _patch_generation(monkeypatch, _generate)

        response = TestClient(app).post(
            "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
            json=_request_body(),
            headers=_headers(),
        )

        assert response.status_code == 502
        assert response.json()["detail"]["code"] == "idea_contract_invalid"


def test_ai_explanation_route_fails_closed_on_served_blank_text(monkeypatch) -> None:
    async def _generate(self, *, candidate_id, **kwargs):
        payload = _served_payload()
        payload["explanation"]["candidateId"] = candidate_id
        payload["explanation"]["explanationText"] = "   "
        return 200, payload

    _patch_generation(monkeypatch, _generate)

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        json=_request_body(),
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_ai_explanation_unsafe"


def test_ai_explanation_readiness_route_fails_closed_on_authority_identity_drift(
    monkeypatch,
) -> None:
    for field, drifted in (
        ("repository", "lotus-core"),
        ("sourceAuthority", "workbench"),
        ("workflowAuthority", "manual"),
    ):

        async def _readiness(self, **kwargs):
            payload = dict(IDEA_AI_EXPLANATION_READINESS_EXAMPLE)
            payload[field] = drifted
            return 200, payload

        monkeypatch.setattr(
            "app.clients.lotus_idea_client.LotusIdeaClient.get_ai_explanation_readiness",
            _readiness,
        )

        response = TestClient(app).get(
            "/api/v1/ideas/ai-explanations/readiness",
            headers=_headers(),
        )

        assert response.status_code == 502
        assert response.json()["detail"]["code"] == "idea_contract_invalid"


def test_ai_explanation_route_fails_closed_on_lax_boolean_authority_claims(monkeypatch) -> None:
    for lax_value in ("false", 0):

        async def _generate(self, *, candidate_id, **kwargs):
            payload = _served_payload()
            payload["explanation"]["candidateId"] = candidate_id
            payload["explanation"]["grantsDownstreamAuthority"] = lax_value
            return 200, payload

        _patch_generation(monkeypatch, _generate)

        response = TestClient(app).post(
            "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
            json=_request_body(),
            headers=_headers(),
        )

        assert response.status_code == 502
        assert response.json()["detail"]["code"] == "idea_contract_invalid"


def test_ai_explanation_readiness_route_fails_closed_on_lax_boolean_claims(monkeypatch) -> None:
    async def _readiness(self, **kwargs):
        payload = dict(IDEA_AI_EXPLANATION_READINESS_EXAMPLE)
        payload["supportedFeaturePromoted"] = "false"
        return 200, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.get_ai_explanation_readiness",
        _readiness,
    )

    response = TestClient(app).get(
        "/api/v1/ideas/ai-explanations/readiness",
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_contract_invalid"


def _served_payload_with_evidence(evidence_mutation) -> dict[str, Any]:
    payload = copy.deepcopy(IDEA_AI_EXPLANATION_EXAMPLE)
    evidence_mutation(payload["explanation"]["redactedEvidence"])
    return payload


def _post_explanation(monkeypatch, payload) -> "TestClient":
    async def _generate(self, *, candidate_id, body, caller_headers, correlation_id, **kwargs):
        return 200, payload

    _patch_generation(monkeypatch, _generate)
    return TestClient(app)


def test_ai_explanation_forwards_redacted_evidence_identity_byte_faithfully(monkeypatch) -> None:
    payload = _served_payload_with_evidence(
        lambda evidence: evidence.update({"sourceCutTolerance": {"maxSkewSeconds": 30}})
    )
    client = _post_explanation(monkeypatch, payload)

    response = client.post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        headers=_headers(),
        json=_request_body(),
    )

    assert response.status_code == 200
    evidence = response.json()["explanation"]["redactedEvidence"]
    assert evidence["evidencePacketId"] == "iep_high_cash_8d57adbf52f7f5a7"
    assert evidence["evidenceContentHash"] == "sha256:evidence-lineage"
    assert evidence["sourceRevisionVectorDigest"] == "sha256:source-revision-vector"
    assert evidence["sourceCutPosture"] == "coherent"
    # Additive source fields survive the typed identity skeleton verbatim.
    assert evidence["sourceCutTolerance"] == {"maxSkewSeconds": 30}


def test_ai_explanation_fails_closed_on_missing_redacted_evidence_identity(monkeypatch) -> None:
    payload = _served_payload_with_evidence(
        lambda evidence: evidence.pop("sourceRevisionVectorDigest")
    )
    client = _post_explanation(monkeypatch, payload)

    response = client.post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        headers=_headers(),
        json=_request_body(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_contract_invalid"


def test_ai_explanation_fails_closed_on_blank_redacted_evidence_identity(monkeypatch) -> None:
    payload = _served_payload_with_evidence(
        lambda evidence: evidence.update({"sourceCutPosture": " "})
    )
    client = _post_explanation(monkeypatch, payload)

    response = client.post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        headers=_headers(),
        json=_request_body(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_contract_invalid"


def test_ai_explanation_fails_closed_on_duplicate_evidence_identity_spelling(monkeypatch) -> None:
    payload = _served_payload_with_evidence(
        lambda evidence: evidence.update({"evidence_content_hash": "sha256:other"})
    )
    client = _post_explanation(monkeypatch, payload)

    response = client.post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        headers=_headers(),
        json=_request_body(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_contract_invalid"


def test_ai_explanation_fails_closed_on_missing_redacted_evidence_envelope(monkeypatch) -> None:
    payload = copy.deepcopy(IDEA_AI_EXPLANATION_EXAMPLE)
    del payload["explanation"]["redactedEvidence"]
    client = _post_explanation(monkeypatch, payload)

    response = client.post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/ai-explanations",
        headers=_headers(),
        json=_request_body(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_contract_invalid"
