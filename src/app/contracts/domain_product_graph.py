from pydantic import BaseModel, Field

from app.contracts.domain_product_failure_posture import (
    DomainProductFailurePostureCondition,
)


class DomainProductGraphNode(BaseModel):
    node_id: str = Field(alias="nodeId", description="Stable graph node identity.")
    node_type: str = Field(alias="nodeType", description="Graph node classification.")
    product_id: str | None = Field(
        default=None,
        alias="productId",
        description="Domain-product id when the node represents a product.",
    )
    product_name: str | None = Field(default=None, alias="productName")
    product_version: str | None = Field(default=None, alias="productVersion")
    producer_repository: str | None = Field(default=None, alias="producerRepository")
    product_family: str | None = Field(default=None, alias="productFamily")
    lifecycle_status: str | None = Field(default=None, alias="lifecycleStatus")
    repository: str | None = Field(default=None, description="Repository name for repo nodes.")

    model_config = {"populate_by_name": True}


class DomainProductGraphEdge(BaseModel):
    edge_type: str = Field(alias="edgeType", description="Graph relationship type.")
    from_node: str = Field(alias="from", description="Source graph node id.")
    to_node: str = Field(alias="to", description="Target graph node id.")
    consumption_mode: str | None = Field(
        default=None,
        alias="consumptionMode",
        description="Consumption mode for dependency edges.",
    )
    failure_posture: str | None = Field(
        default=None,
        alias="failurePosture",
        description="Failure posture for dependency edges.",
    )
    failure_posture_conditions: list[DomainProductFailurePostureCondition] = Field(
        default_factory=list,
        alias="failurePostureConditions",
        description="Conditional failure-posture overrides for dependency edges.",
    )
    validation_lanes: list[str] = Field(
        default_factory=list,
        alias="validationLanes",
        description="Validation lanes that cover dependency edges.",
    )

    model_config = {"populate_by_name": True}


class DomainProductGraphData(BaseModel):
    consumer_system: str = Field(alias="consumerSystem", description="Caller identity.")
    correlation_id: str = Field(alias="correlationId", description="Correlation id.")
    contract_id: str = Field(alias="contractId", description="Graph contract id.")
    contract_version: str = Field(alias="contractVersion", description="Graph contract version.")
    generated_at_utc: str = Field(
        alias="generatedAtUtc",
        description="UTC timestamp when the dependency graph artifact was generated.",
    )
    source_catalog: str = Field(
        alias="sourceCatalog",
        description="Source catalog artifact used to generate the dependency graph.",
    )
    governed_by_rfcs: list[str] = Field(
        alias="governedByRfcs",
        description="Platform RFCs that govern dependency graph generation and publication.",
    )
    node_count: int = Field(alias="nodeCount", description="Number of graph nodes.")
    edge_count: int = Field(alias="edgeCount", description="Number of graph edges.")
    nodes: list[DomainProductGraphNode] = Field(description="Domain-product graph nodes.")
    edges: list[DomainProductGraphEdge] = Field(description="Domain-product graph edges.")

    model_config = {"populate_by_name": True}


class DomainProductGraphResponse(BaseModel):
    data: DomainProductGraphData = Field(
        description="Gateway discovery view over the platform dependency graph."
    )
