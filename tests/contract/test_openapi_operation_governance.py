from typing import Any

from fastapi.testclient import TestClient

from app.main import app

OPENAPI_METHODS = {"delete", "get", "patch", "post", "put"}


def _operation_id(path: str, method: str, operation: dict[str, Any]) -> str:
    return f"{method.upper()} {path} ({operation.get('operationId', '<missing-id>')})"


def test_public_operations_document_description_tags_and_errors() -> None:
    spec = TestClient(app).get("/openapi.json").json()

    missing_descriptions: list[str] = []
    missing_tags: list[str] = []
    missing_error_responses: list[str] = []

    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method not in OPENAPI_METHODS:
                continue

            operation_name = _operation_id(path, method, operation)
            if not str(operation.get("description", "")).strip():
                missing_descriptions.append(operation_name)
            if not operation.get("tags"):
                missing_tags.append(operation_name)
            response_codes = {str(code) for code in operation.get("responses", {})}
            if not any(code.startswith(("4", "5")) for code in response_codes):
                missing_error_responses.append(operation_name)

    assert missing_descriptions == []
    assert missing_tags == []
    assert missing_error_responses == []


def test_public_operation_tags_have_global_descriptions() -> None:
    spec = TestClient(app).get("/openapi.json").json()

    operation_tags = {
        tag
        for path_item in spec["paths"].values()
        for method, operation in path_item.items()
        if method in OPENAPI_METHODS
        for tag in operation.get("tags", [])
    }
    global_tag_descriptions = {
        tag["name"]: tag.get("description", "") for tag in spec.get("tags", [])
    }

    assert sorted(operation_tags - set(global_tag_descriptions)) == []
    assert [tag for tag in sorted(operation_tags) if not global_tag_descriptions[tag].strip()] == []
