from fastapi.testclient import TestClient

from app.main import app


def test_ideas_openapi_contract_registered() -> None:
    spec = TestClient(app).get("/openapi.json").json()

    queue_operation = spec["paths"]["/api/v1/ideas/review-queues/advisor"]["get"]
    detail_operation = spec["paths"]["/api/v1/ideas/candidates/{candidate_id}"]["get"]
    review_action_operation = spec["paths"][
        "/api/v1/ideas/candidates/{candidate_id}/review-actions"
    ]["post"]
    feedback_operation = spec["paths"]["/api/v1/ideas/candidates/{candidate_id}/feedback"]["post"]
    presentation_operation = spec["paths"][
        "/api/v1/ideas/candidates/{candidate_id}/presentation-receipts"
    ]["post"]
    conversion_operation = spec["paths"][
        "/api/v1/ideas/candidates/{candidate_id}/conversion-intents"
    ]["post"]
    queue_schema = spec["components"]["schemas"]["IdeaGatewayReviewQueueResponse"]
    queue_candidate_schema = spec["components"]["schemas"][
        "IdeaGatewayReviewQueueCandidateResponse"
    ]
    detail_schema = spec["components"]["schemas"]["IdeaGatewayCandidateDetailResponse"]

    assert queue_operation["summary"] == "Get advisor idea review queue"
    assert detail_operation["summary"] == "Get idea candidate detail"
    assert "lotus-idea" in queue_operation["description"]
    assert "does not rank" in queue_operation["description"]
    queue_parameter_names = {parameter["name"] for parameter in queue_operation["parameters"]}
    detail_parameter_names = {parameter["name"] for parameter in detail_operation["parameters"]}
    assert {
        "X-Caller-Tenant-Ids",
        "X-Caller-Book-Ids",
        "X-Caller-Portfolio-Ids",
        "X-Caller-Client-Ids",
    }.issubset(queue_parameter_names)
    assert {
        "X-Caller-Tenant-Ids",
        "X-Caller-Book-Ids",
        "X-Caller-Portfolio-Ids",
        "X-Caller-Client-Ids",
    }.issubset(detail_parameter_names)
    assert "does not enrich" in detail_operation["description"]
    assert "entitlement-scope" in detail_operation["description"]
    assert queue_operation["responses"]["403"]["description"]
    assert queue_operation["responses"]["502"]["description"]
    assert detail_operation["responses"]["404"]["description"]
    assert detail_operation["responses"]["502"]["description"]
    assert queue_schema["properties"]["supportedFeaturePromoted"]["description"]
    assert {"candidateId", "materialVersion", "evidenceVersion"}.issubset(
        queue_candidate_schema["required"]
    )
    assert detail_schema["properties"]["evidence"]["description"]
    assert detail_schema["properties"]["supportedFeaturePromoted"]["description"]
    assert review_action_operation["summary"] == "Record idea candidate review action"
    assert feedback_operation["summary"] == "Record idea candidate feedback"
    assert presentation_operation["summary"] == "Record visible idea candidate presentation"
    assert conversion_operation["summary"] == "Record idea candidate conversion intent"
    for operation in (review_action_operation, feedback_operation, conversion_operation):
        parameter_names = {parameter["name"] for parameter in operation["parameters"]}
        assert {"Idempotency-Key", "X-Causation-Id", "X-Caller-Capabilities"}.issubset(
            parameter_names
        )
        example = operation["responses"]["200"]["content"]["application/json"]["example"]
        assert example["durableStorageBacked"] is True
        assert example["supportedFeaturePromoted"] is False
        assert "client communication" not in str(example).lower()
        assert operation["responses"]["409"]["description"]
        assert operation["responses"]["422"]["description"]
        assert operation["responses"]["502"]["description"]
        assert "does not" in operation["description"]
    assert (
        review_action_operation["responses"]["200"]["content"]["application/json"]["example"][
            "reviewDecision"
        ]["grantsDownstreamAuthority"]
        is False
    )
    assert (
        conversion_operation["responses"]["200"]["content"]["application/json"]["example"][
            "conversionIntent"
        ]["grantsDownstreamAuthority"]
        is False
    )
    feedback_example = feedback_operation["responses"]["200"]["content"]["application/json"][
        "example"
    ]["feedbackEvent"]
    assert feedback_example["taxonomyVersion"] == "idea-feedback-taxonomy-v1"
    assert feedback_example["reason"] == "relevant"
    assert "reasonCodes" not in feedback_example
    queue_candidate = queue_operation["responses"]["200"]["content"]["application/json"]["example"][
        "items"
    ][0]["candidate"]
    assert (queue_candidate["materialVersion"], queue_candidate["evidenceVersion"]) == (1, 1)
    presentation_parameters = {
        parameter["name"] for parameter in presentation_operation["parameters"]
    }
    assert {"Idempotency-Key", "X-Causation-Id", "X-Caller-Tenant-Ids"}.issubset(
        presentation_parameters
    )
    assert (
        "Queue retrieval and prefetch never create presentation evidence"
        in (presentation_operation["description"])
    )
    assert (
        presentation_operation["responses"]["200"]["content"]["application/json"]["example"][
            "persistenceDecision"
        ]
        == "replayed"
    )
    accepted_receipt = presentation_operation["responses"]["201"]["content"]["application/json"][
        "example"
    ]
    assert accepted_receipt["persistenceDecision"] == "accepted"
    assert accepted_receipt["supportedFeaturePromoted"] is False
    assert presentation_operation["responses"]["503"]["description"]
