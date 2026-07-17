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
    conversion_operation = spec["paths"][
        "/api/v1/ideas/candidates/{candidate_id}/conversion-intents"
    ]["post"]
    queue_schema = spec["components"]["schemas"]["IdeaGatewayReviewQueueResponse"]
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
    assert detail_schema["properties"]["evidence"]["description"]
    assert detail_schema["properties"]["supportedFeaturePromoted"]["description"]
    assert review_action_operation["summary"] == "Record idea candidate review action"
    assert feedback_operation["summary"] == "Record idea candidate feedback"
    assert conversion_operation["summary"] == "Record idea candidate conversion intent"
    for operation in (review_action_operation, feedback_operation, conversion_operation):
        parameter_names = {parameter["name"] for parameter in operation["parameters"]}
        assert {"Idempotency-Key", "X-Causation-Id", "X-Caller-Capabilities"}.issubset(
            parameter_names
        )
        assert operation["responses"]["409"]["description"]
        assert operation["responses"]["422"]["description"]
        assert operation["responses"]["502"]["description"]
        assert "does not" in operation["description"]
