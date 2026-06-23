from fastapi.testclient import TestClient

from app.main import app


def test_ideas_openapi_contract_registered() -> None:
    spec = TestClient(app).get("/openapi.json").json()

    queue_operation = spec["paths"]["/api/v1/ideas/review-queues/advisor"]["get"]
    detail_operation = spec["paths"]["/api/v1/ideas/candidates/{candidate_id}"]["get"]
    queue_schema = spec["components"]["schemas"]["IdeaGatewayReviewQueueResponse"]
    detail_schema = spec["components"]["schemas"]["IdeaGatewayCandidateDetailResponse"]

    assert queue_operation["summary"] == "Get advisor idea review queue"
    assert detail_operation["summary"] == "Get idea candidate detail"
    assert "lotus-idea" in queue_operation["description"]
    assert "does not rank" in queue_operation["description"]
    queue_parameter_names = {parameter["name"] for parameter in queue_operation["parameters"]}
    assert {
        "X-Caller-Tenant-Ids",
        "X-Caller-Book-Ids",
        "X-Caller-Portfolio-Ids",
        "X-Caller-Client-Ids",
    }.issubset(queue_parameter_names)
    assert "does not enrich" in detail_operation["description"]
    assert queue_operation["responses"]["403"]["description"]
    assert queue_operation["responses"]["502"]["description"]
    assert detail_operation["responses"]["404"]["description"]
    assert detail_operation["responses"]["502"]["description"]
    assert queue_schema["properties"]["supportedFeaturePromoted"]["description"]
    assert detail_schema["properties"]["evidence"]["description"]
    assert detail_schema["properties"]["supportedFeaturePromoted"]["description"]
