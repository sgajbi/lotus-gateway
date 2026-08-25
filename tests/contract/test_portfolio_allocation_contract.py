from copy import deepcopy
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _assert_closed_allocation_schema_graph(schemas: dict[str, Any]) -> set[str]:
    roots = {"PortfolioAllocationResponse"}
    visited: set[str] = set()

    def visit_fragment(fragment: object, path: str, pending: list[str]) -> None:
        if not isinstance(fragment, dict):
            return
        if fragment.get("type") == "object":
            assert fragment.get("additionalProperties") is False, (
                f"{path}.additionalProperties must be false"
            )
        ref = fragment.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/PortfolioAllocation"):
            pending.append(ref.rsplit("/", 1)[-1])
        for key in ("anyOf", "allOf", "oneOf"):
            for index, child in enumerate(fragment.get(key, [])):
                visit_fragment(child, f"{path}.{key}[{index}]", pending)
        visit_fragment(fragment.get("items"), f"{path}.items", pending)
        additional_properties = fragment.get("additionalProperties")
        if isinstance(additional_properties, dict):
            visit_fragment(additional_properties, f"{path}.additionalProperties", pending)
        for property_name, property_schema in fragment.get("properties", {}).items():
            visit_fragment(property_schema, f"{path}.{property_name}", pending)

    pending = list(roots)
    while pending:
        schema_name = pending.pop()
        if schema_name in visited:
            continue
        assert schema_name in schemas, schema_name
        visited.add(schema_name)
        schema = schemas[schema_name]
        assert schema.get("additionalProperties") is False, schema_name
        assert schema.get("properties"), schema_name
        for property_name, property_schema in schema["properties"].items():
            visit_fragment(property_schema, f"{schema_name}.{property_name}", pending)

    return visited


def test_portfolio_allocation_openapi_graph_is_closed_and_typed() -> None:
    schemas = TestClient(app).get("/openapi.json").json()["components"]["schemas"]

    visited = _assert_closed_allocation_schema_graph(schemas)

    assert visited == {
        "PortfolioAllocationBucket",
        "PortfolioAllocationContributor",
        "PortfolioAllocationLookThroughCapability",
        "PortfolioAllocationResponse",
        "PortfolioAllocationView",
    }


def test_portfolio_allocation_openapi_fitness_rejects_nested_free_form_objects() -> None:
    schemas = deepcopy(TestClient(app).get("/openapi.json").json()["components"]["schemas"])
    schemas["PortfolioAllocationContributor"]["additionalProperties"] = True

    with pytest.raises(
        AssertionError,
        match=r"PortfolioAllocationContributor",
    ):
        _assert_closed_allocation_schema_graph(schemas)
